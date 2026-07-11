module daily_limit_checker(
    input  [15:0] transaction_amount,
    input  [15:0] daily_total_before,
    input  [15:0] daily_limit,
    input  [15:0] single_txn_limit,
    output        daily_limit_violation,
    output        single_txn_violation,
    output        limit_violation
);

wire [16:0] projected_daily_total;

assign projected_daily_total   = {1'b0, daily_total_before} + {1'b0, transaction_amount};
assign daily_limit_violation   = projected_daily_total > {1'b0, daily_limit};
assign single_txn_violation    = transaction_amount > single_txn_limit;
assign limit_violation         = daily_limit_violation | single_txn_violation;

endmodule
