/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*==========================================================================*/
/* File containing the implementation of the device clocks.                 */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "dev_sm.h"

/* Local defines */

/* Local types */

/* Local variables */

static bool s_clockState[DEV_SM_NUM_CLOCK];
static uint64_t s_clockFreq[DEV_SM_NUM_CLOCK];
static uint32_t s_clockParent[DEV_SM_NUM_CLOCK];
static uint32_t s_clockSscConfig[DEV_SM_NUM_CLOCK];

/*--------------------------------------------------------------------------*/
/* Return clock name                                                        */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockNameGet(uint32_t clockId, string *clockNameAddr,
    int32_t *len)
{
    int32_t status = SM_ERR_SUCCESS;
    static int32_t s_maxLen = 0;

    static string const s_name[DEV_SM_NUM_CLOCK] =
    {
        [DEV_SM_CLK_0] = "clk0",
        [DEV_SM_CLK_1] = "clk1",
        [DEV_SM_CLK_2] = "clk2",
        [DEV_SM_CLK_3] = "clk3",
        [DEV_SM_CLK_5] = "clk5"
    };

    /* Get max string width */
    DEV_SM_MaxStringGet(len, &s_maxLen, s_name, DEV_SM_NUM_CLOCK);

    /* Check clock */
    if ((clockId >= DEV_SM_NUM_CLOCK) || DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        /* Return pointer to name */
        *clockNameAddr = s_name[clockId];
    }

    SM_TEST_MODE_ERR(SM_TEST_MODE_DEV_LVL1, SM_ERR_TEST)

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Return supported clock range                                             */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockDescribe(uint32_t clockId,
    dev_sm_clock_range_t *range)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if ((clockId >= DEV_SM_NUM_CLOCK) || DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        /* Return range */
        range->lowestRate = 625000000U;
        range->highestRate = 1200000000U;
        range->stepSize = 1U;
    }

    SM_TEST_MODE_ERR(SM_TEST_MODE_DEV_LVL2, SM_ERR_TEST)

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Return clock parent info                                                 */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockParentDescribe(uint32_t clockId, uint32_t sel,
    uint32_t *parentId, uint32_t *numParents)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else if (clockId == DEV_SM_CLK_0)
    {
        /* Return mux input and max number */
        status = SM_ERR_NOT_SUPPORTED;
        *numParents = 0U;
    }
    else if (clockId == DEV_SM_CLK_2)
    {
        if (sel == 0U)
        {
            /* Return mux input and max number */
            *parentId = DEV_SM_CLK_0;
            *numParents = 2U;
        }
        else if (sel == 1U)
        {
            /* Return mux input and max number */
            *parentId = DEV_SM_CLK_1;
            *numParents = 2U;
        }
        else
        {
            /* Return mux input and max number */
            status = SM_ERR_OUT_OF_RANGE;
            *numParents = 2U;
        }
    }
    else if (clockId < DEV_SM_NUM_CLOCK)
    {
        /* Return mux input and max number */
        if (sel == 0U)
        {
            *parentId = DEV_SM_CLK_0;
            *numParents = 1U;
        }
        else
        {
            status = SM_ERR_OUT_OF_RANGE;
            *numParents = 1U;
        }
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set clock rate                                                           */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockRateSet(uint32_t clockId, uint64_t rate,
    uint32_t roundSel)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else if (clockId < DEV_SM_NUM_CLOCK)
    {
        if (roundSel <= 2U)
        {
            s_clockFreq[clockId] = rate;
        }
        else
        {
            status = SM_ERR_INVALID_PARAMETERS;
        }
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get clock rate                                                           */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockRateGet(uint32_t clockId, uint64_t *rate)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else if (clockId < DEV_SM_NUM_CLOCK)
    {
        *rate = s_clockFreq[clockId];
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Enable/disable clock                                                     */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockEnable(uint32_t clockId, bool enable)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else if (clockId < DEV_SM_NUM_CLOCK)
    {
        s_clockState[clockId] = enable;
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Return clock enable status                                               */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockIsEnabled(uint32_t clockId, bool *enabled)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else if (clockId < DEV_SM_NUM_CLOCK)
    {
        *enabled = s_clockState[clockId];
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set clock parent                                                         */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockParentSet(uint32_t clockId, uint32_t parent)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else if (clockId == DEV_SM_CLK_0)
    {
        status = SM_ERR_INVALID_PARAMETERS;
    }
    else if (clockId < DEV_SM_NUM_CLOCK)
    {
        s_clockParent[clockId] = parent;
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get clock parent                                                         */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockParentGet(uint32_t clockId, uint32_t *parent)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else if (clockId == DEV_SM_CLK_0)
    {
        status = SM_ERR_INVALID_PARAMETERS;
    }
    else if (clockId < DEV_SM_NUM_CLOCK)
    {
        *parent = s_clockParent[clockId];
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    SM_TEST_MODE_ERR(SM_TEST_MODE_DEV_LVL2, SM_ERR_TEST)

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get extended clock info                                                  */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockExtendedInfo(uint32_t clockId, bool *supported)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        /* Check if SCC is supported */
        *supported = (clockId < DEV_SM_NUM_CLOCK);
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set a device extended clock data value                                   */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockExtendedSet(uint32_t clockId, uint32_t extId,
    uint32_t extConfigValue)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        switch (extId)
        {
            case DEV_SM_CLOCK_EXT_SSC:
                if (clockId < DEV_SM_NUM_CLOCK)
                {
                    /* Latch SSC configuration */
                    s_clockSscConfig[clockId] = extConfigValue;
                }
                else
                {
                    status = SM_ERR_INVALID_PARAMETERS;
                }
                break;

            default:
                status = SM_ERR_NOT_FOUND;
                break;
        }
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set a device extended clock data value                                   */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ClockExtendedGet(uint32_t clockId, uint32_t extId,
    uint32_t *extConfigValue)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check clock */
    if (DEV_SM_ClockIsReserved(clockId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        switch (extId)
        {
            /* Spread spectrum */
            case DEV_SM_CLOCK_EXT_SSC:
                if (clockId < DEV_SM_NUM_CLOCK)
                {
                    /* Get latched SSC configuration */
                    *extConfigValue = s_clockSscConfig[clockId];
                }
                else
                {
                    status = SM_ERR_INVALID_PARAMETERS;
                }
                break;

            default:
                status = SM_ERR_NOT_FOUND;
                break;
        }
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Check if clock domain is reserved                                        */
/*--------------------------------------------------------------------------*/
bool DEV_SM_ClockIsReserved(uint32_t clockId)
{
    bool rc = false;
    static bool const s_clockIsReserved[DEV_SM_NUM_CLOCK] =
    {
        [DEV_SM_CLK_4] = true
    };


    if (clockId < DEV_SM_NUM_CLOCK)
    {
        rc = s_clockIsReserved[clockId];
    }

    return rc;
}

