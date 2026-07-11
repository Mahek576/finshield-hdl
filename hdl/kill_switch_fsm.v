module kill_switch_fsm(
    input        clk,
    input        reset_n,
    input        txn_valid,
    input        warn_condition,
    input        block_condition,
    input        clear_lock,
    input        cooldown_done,
    output reg [1:0] state,
    output       allow_transaction,
    output       step_up_auth_required,
    output       kill_switch_active,
    output       audit_event
);

localparam NORMAL   = 2'b00;
localparam WARNING  = 2'b01;
localparam LOCKED   = 2'b10;
localparam COOLDOWN = 2'b11;

reg [1:0] next_state;

always @(*) begin
    next_state = state;

    case (state)
        NORMAL: begin
            if (block_condition)
                next_state = LOCKED;
            else if (warn_condition)
                next_state = WARNING;
            else
                next_state = NORMAL;
        end

        WARNING: begin
            if (block_condition)
                next_state = LOCKED;
            else if (clear_lock)
                next_state = NORMAL;
            else if (!warn_condition)
                next_state = NORMAL;
            else
                next_state = WARNING;
        end

        LOCKED: begin
            if (clear_lock)
                next_state = COOLDOWN;
            else
                next_state = LOCKED;
        end

        COOLDOWN: begin
            if (cooldown_done)
                next_state = NORMAL;
            else
                next_state = COOLDOWN;
        end

        default: begin
            next_state = NORMAL;
        end
    endcase
end

always @(posedge clk or negedge reset_n) begin
    if (!reset_n)
        state <= NORMAL;
    else
        state <= next_state;
end

assign allow_transaction     = ((state == NORMAL) | (state == WARNING)) & !block_condition;
assign step_up_auth_required = (state == WARNING) | warn_condition;
assign kill_switch_active    = (state == LOCKED);
assign audit_event           = txn_valid & (warn_condition | block_condition | (state != NORMAL));

endmodule
