# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

import numpy as np
cimport numpy as cnp

cpdef str construct_fix_order_message(str account_id, str target_id, str side, double price, double qty):
    """
    Constructs raw institutional FIX 4.4 Message Frame with absolute zero overhead
    35=D (New Order Single), 54=1 (Buy) or 2 (Sell), 38=Quantity, 44=Price
    """
    cdef str fix_msg = f"8=FIX.4.4|9=145|35=D|49={account_id}|56={target_id}|11=SND_{np.random.randint(100000)}|21=1|55=XAUUSD|"
    if side.upper() == "BUY":
        fix_msg += "54=1|"
    else:
        fix_msg += "54=2|"
    fix_msg += f"38={qty}|40=2|44={price}|59=0|10=220|"
    return fix_msg.replace("|", chr(1))
