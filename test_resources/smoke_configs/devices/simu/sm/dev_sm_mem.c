/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*==========================================================================*/
/* File containing the implementation of the device memory.                 */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "dev_sm.h"

/* Local defines */

/* Local types */

/* Local variables */

/* Local functions */

/*--------------------------------------------------------------------------*/
/* Return DDR memory region info                                            */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_MemDdrInfoGet(uint32_t ddrRgdId, uint32_t *numRgd,
    uint32_t *ddrType, uint32_t *ddrWidth, bool *eccEnb, uint32_t *mts,
    uint64_t *startAddr, uint64_t *endAddr)
{
    *numRgd = 2U;

    if (ddrRgdId == 0U)
    {
        *ddrType = DEV_SM_DDR_TYPE_LPDDR5;
        *ddrWidth = 32U;
        *eccEnb = false;
        *mts = 8400U;
        *startAddr = 0x80000000ULL;
        *endAddr = 0xFFFFFFFFULL;
    }
    else
    {
        *ddrType = DEV_SM_DDR_TYPE_LPDDR4X;
        *ddrWidth = 16U;
        *eccEnb = true;
        *mts = 4000U;
        *startAddr = 0x100000000ULL;
        *endAddr = 0x1FFFFFFFFULL;
    }

    /* Return status */
    return SM_ERR_SUCCESS;
}

