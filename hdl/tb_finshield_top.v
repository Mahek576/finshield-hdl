`timescale 1ns/1ps

module tb_finshield_top;

reg clk;
reg reset_n;
reg txn_valid;

reg [15:0] transaction_amount;
reg [15:0] daily_total_before;
reg [7:0]  txn_count_window;

reg [7:0] risk_score;
reg [7:0] ml_confidence_score;
reg anomaly_flag;

reg new_device;
reg foreign_ip;
reg multiple_failed_logins;

reg clear_lock;
reg cooldown_done;

wire allow_transaction;
wire step_up_auth_required;
wire kill_switch_active;
wire audit_event;

wire [1:0] fsm_state;
wire [1:0] final_decision;

wire limit_violation;
wire velocity_violation;
wire risk_warn_flag;
wire risk_block_flag;
wire ato_suspected;
wire low_confidence;

integer pass_count;
integer fail_count;

finshield_top dut(
    .clk(clk),
    .reset_n(reset_n),
    .txn_valid(txn_valid),
    .transaction_amount(transaction_amount),
    .daily_total_before(daily_total_before),
    .txn_count_window(txn_count_window),
    .risk_score(risk_score),
    .ml_confidence_score(ml_confidence_score),
    .anomaly_flag(anomaly_flag),
    .new_device(new_device),
    .foreign_ip(foreign_ip),
    .multiple_failed_logins(multiple_failed_logins),
    .clear_lock(clear_lock),
    .cooldown_done(cooldown_done),
    .allow_transaction(allow_transaction),
    .step_up_auth_required(step_up_auth_required),
    .kill_switch_active(kill_switch_active),
    .audit_event(audit_event),
    .fsm_state(fsm_state),
    .final_decision(final_decision),
    .limit_violation(limit_violation),
    .velocity_violation(velocity_violation),
    .risk_warn_flag(risk_warn_flag),
    .risk_block_flag(risk_block_flag),
    .ato_suspected(ato_suspected),
    .low_confidence(low_confidence)
);

always #5 clk = ~clk;

task apply_transaction;
    input [15:0] amount;
    input [15:0] daily_total;
    input [7:0] velocity;
    input [7:0] risk;
    input [7:0] confidence;
    input anomaly;
    input device;
    input ip;
    input failed_logins;
    begin
        transaction_amount = amount;
        daily_total_before = daily_total;
        txn_count_window = velocity;
        risk_score = risk;
        ml_confidence_score = confidence;
        anomaly_flag = anomaly;
        new_device = device;
        foreign_ip = ip;
        multiple_failed_logins = failed_logins;
        txn_valid = 1'b1;
        #20;
        txn_valid = 1'b0;
    end
endtask

task check_decision;
    input [1:0] expected_decision;
    input expected_allow;
    input expected_kill;
    begin
        #1;
        if ((final_decision == expected_decision) &&
            (allow_transaction == expected_allow) &&
            (kill_switch_active == expected_kill)) begin
            pass_count = pass_count + 1;
            $display("PASS time=%0t decision=%b allow=%b kill=%b state=%b", $time, final_decision, allow_transaction, kill_switch_active, fsm_state);
        end else begin
            fail_count = fail_count + 1;
            $display("FAIL time=%0t expected_decision=%b actual_decision=%b expected_allow=%b actual_allow=%b expected_kill=%b actual_kill=%b state=%b",
                     $time, expected_decision, final_decision, expected_allow, allow_transaction, expected_kill, kill_switch_active, fsm_state);
        end
    end
endtask

initial begin
    $dumpfile("finshield_top.vcd");
    $dumpvars(0, tb_finshield_top);

    clk = 1'b0;
    reset_n = 1'b0;
    txn_valid = 1'b0;

    transaction_amount = 16'd0;
    daily_total_before = 16'd0;
    txn_count_window = 8'd0;
    risk_score = 8'd0;
    ml_confidence_score = 8'd100;
    anomaly_flag = 1'b0;
    new_device = 1'b0;
    foreign_ip = 1'b0;
    multiple_failed_logins = 1'b0;
    clear_lock = 1'b0;
    cooldown_done = 1'b0;

    pass_count = 0;
    fail_count = 0;

    #20;
    reset_n = 1'b1;
    #10;

    $display("CASE 1: Safe transaction should be approved");
    apply_transaction(16'd500, 16'd1000, 8'd1, 8'd20, 8'd95, 1'b0, 1'b0, 1'b0, 1'b0);
    check_decision(2'b00, 1'b1, 1'b0);

    $display("CASE 2: Medium risk transaction should require review");
    apply_transaction(16'd1200, 16'd2000, 8'd2, 8'd65, 8'd80, 1'b0, 1'b0, 1'b0, 1'b0);
    check_decision(2'b01, 1'b1, 1'b0);

    $display("CASE 3: High risk transaction should activate kill switch");
    apply_transaction(16'd1500, 16'd2500, 8'd2, 8'd90, 8'd70, 1'b0, 1'b0, 1'b0, 1'b0);
    check_decision(2'b10, 1'b0, 1'b1);

    $display("CASE 4: Clear lock and return through cooldown");
    clear_lock = 1'b1;
    #20;
    clear_lock = 1'b0;
    cooldown_done = 1'b1;
    #20;
    cooldown_done = 1'b0;
    apply_transaction(16'd700, 16'd2000, 8'd1, 8'd25, 8'd90, 1'b0, 1'b0, 1'b0, 1'b0);
    check_decision(2'b00, 1'b1, 1'b0);

    $display("CASE 5: Daily limit violation should block");
    apply_transaction(16'd4000, 16'd9000, 8'd1, 8'd30, 8'd90, 1'b0, 1'b0, 1'b0, 1'b0);
    check_decision(2'b10, 1'b0, 1'b1);

    $display("CASE 6: Account takeover pattern should block");
    clear_lock = 1'b1;
    #20;
    clear_lock = 1'b0;
    cooldown_done = 1'b1;
    #20;
    cooldown_done = 1'b0;
    apply_transaction(16'd600, 16'd1000, 8'd1, 8'd45, 8'd80, 1'b0, 1'b1, 1'b1, 1'b0);
    check_decision(2'b10, 1'b0, 1'b1);

    $display("SUMMARY passed=%0d failed=%0d", pass_count, fail_count);

    #20;
    $finish;
end

endmodule
