module risk_threshold_checker(
    input  [7:0] risk_score,
    input  [7:0] warn_threshold,
    input  [7:0] block_threshold,
    output       risk_warn_flag,
    output       risk_block_flag
);

assign risk_warn_flag  = risk_score >= warn_threshold;
assign risk_block_flag = risk_score >= block_threshold;

endmodule
