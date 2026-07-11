module account_takeover_checker(
    input new_device,
    input foreign_ip,
    input multiple_failed_logins,
    input anomaly_flag,
    input risk_block_flag,
    output ato_suspected
);

assign ato_suspected =
    (new_device & foreign_ip) |
    (multiple_failed_logins & anomaly_flag) |
    (new_device & anomaly_flag & risk_block_flag);

endmodule
