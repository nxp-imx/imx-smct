/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*==========================================================================*/
/* File containing the implementation of the device reset domains.          */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "dev_sm.h"

/* Local defines */

/* Local types */

/* Local variables */

static bool s_resetState[DEV_SM_NUM_RESET];

/*--------------------------------------------------------------------------*/
/* Return reset domain name                                                 */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ResetDomainNameGet(uint32_t domainId, string *domainNameAddr,
    int32_t *len)
{
    int32_t status = SM_ERR_SUCCESS;
    static int32_t s_maxLen = 0;

    static string const s_name[DEV_SM_NUM_RESET] =
    {
        [DEV_SM_RST_0] = "rst0",
        [DEV_SM_RST_1] = "rst1",
        [DEV_SM_RST_2] = "rst2",
    };

    /* Get max string width */
    DEV_SM_MaxStringGet(len, &s_maxLen, s_name, DEV_SM_NUM_RESET);

    /* Check reset */
    if (DEV_SM_ResetIsReserved(domainId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        /* Return pointer to name */
        *domainNameAddr = s_name[domainId];
    }

    SM_TEST_MODE_ERR(SM_TEST_MODE_DEV_LVL1, SM_ERR_TEST)

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Reset domain                                                             */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ResetDomain(uint32_t domainId, uint32_t resetState,
    bool toggle, bool assertNegate)
{
    int32_t status = SM_ERR_SUCCESS;

    if (!DEV_SM_ResetIsReserved(domainId))
    {
        if (assertNegate && !toggle)
        {
            s_resetState[domainId] = true;
        }
        else
        {
            s_resetState[domainId] = false;
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
/* Get reset domain status                                                  */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_ResetDomainGet(uint32_t domainId, bool *assertNegate)
{
    int32_t status = SM_ERR_SUCCESS;

    if (!DEV_SM_ResetIsReserved(domainId))
    {
        *assertNegate = s_resetState[domainId];
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Check if PD/CPU is disabled in fuses                                     */
/*--------------------------------------------------------------------------*/
bool DEV_SM_ResetIsReserved(uint32_t domainId)
{
    bool rc = false;

    if (domainId >= DEV_SM_NUM_RESET)
    {
        rc = true;
    }

    return rc;
}

