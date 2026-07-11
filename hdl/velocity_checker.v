module velocity_checker(
    input  [7:0] txn_count_window,
    input  [7:0] max_txn_window,
    output       velocity_violation
);

assign velocity_violation = txn_count_window > max_txn_window;

endmodule
