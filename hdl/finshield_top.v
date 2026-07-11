module finshield_top(
    input        clk,
    input        reset_n,
    input        txn_valid,

    input [15:0] transaction_amount,
    input [15:0] daily_total_before,
    input [7:0]  txn_count_window,

    input [7:0]  risk_score,
    input [7:0]  ml_confidence_score,
    input        anomaly_flag,

    input        new_device,
    input        foreign_ip,
    input        multiple_failed_logins,

    input        clear_lock,
    input        cooldown_done,

    output       allow_transaction,
    output       step_up_auth_required,
    output       kill_switch_active,
    output       audit_event,

    output [1:0] fsm_state,
    output [1:0] final_decision,

    output       limit_violation,
    output       velocity_violation,
    output       risk_warn_flag,
    output       risk_block_flag,
    output       ato_suspected,
    output       low_confidence
);

wire daily_limit_violation;
wire single_txn_violation;

wire warn_condition;
wire block_condition;

localparam [15:0] DAILY_LIMIT      = 16'd10000;
localparam [15:0] SINGLE_TXN_LIMIT = 16'd3000;
localparam [7:0]  MAX_TXN_WINDOW   = 8'd5;
localparam [7:0]  RISK_WARN_LEVEL  = 8'd60;
localparam [7:0]  RISK_BLOCK_LEVEL = 8'd80;
localparam [7:0]  CONF_MIN_LEVEL   = 8'd50;

daily_limit_checker u_daily_limit_checker(
    .transaction_amount(transaction_amount),
    .daily_total_before(daily_total_before),
    .daily_limit(DAILY_LIMIT),
    .single_txn_limit(SINGLE_TXN_LIMIT),
    .daily_limit_violation(daily_limit_violation),
    .single_txn_violation(single_txn_violation),
    .limit_violation(limit_violation)
);

velocity_checker u_velocity_checker(
    .txn_count_window(txn_count_window),
    .max_txn_window(MAX_TXN_WINDOW),
    .velocity_violation(velocity_violation)
);

risk_threshold_checker u_risk_threshold_checker(
    .risk_score(risk_score),
    .warn_threshold(RISK_WARN_LEVEL),
    .block_threshold(RISK_BLOCK_LEVEL),
    .risk_warn_flag(risk_warn_flag),
    .risk_block_flag(risk_block_flag)
);

assign low_confidence = ml_confidence_score < CONF_MIN_LEVEL;

account_takeover_checker u_account_takeover_checker(
    .new_device(new_device),
    .foreign_ip(foreign_ip),
    .multiple_failed_logins(multiple_failed_logins),
    .anomaly_flag(anomaly_flag),
    .risk_block_flag(risk_block_flag),
    .ato_suspected(ato_suspected)
);

assign warn_condition =
    risk_warn_flag |
    anomaly_flag |
    velocity_violation |
    limit_violation |
    low_confidence |
    ato_suspected;

assign block_condition =
    risk_block_flag |
    limit_violation |
    ato_suspected |
    (anomaly_flag & low_confidence);

kill_switch_fsm u_kill_switch_fsm(
    .clk(clk),
    .reset_n(reset_n),
    .txn_valid(txn_valid),
    .warn_condition(warn_condition),
    .block_condition(block_condition),
    .clear_lock(clear_lock),
    .cooldown_done(cooldown_done),
    .state(fsm_state),
    .allow_transaction(allow_transaction),
    .step_up_auth_required(step_up_auth_required),
    .kill_switch_active(kill_switch_active),
    .audit_event(audit_event)
);

assign final_decision =
    (kill_switch_active | block_condition) ? 2'b10 :
    (step_up_auth_required | warn_condition) ? 2'b01 :
    2'b00;

endmodule
