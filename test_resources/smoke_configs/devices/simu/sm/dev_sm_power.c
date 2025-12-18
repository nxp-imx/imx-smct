/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*==========================================================================*/
/* File containing the implementation of the device power domains.          */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "dev_sm.h"

/* Local defines */

/* Local types */

/* Local variables */

static uint8_t s_powerState[DEV_SM_NUM_POWER];

/*--------------------------------------------------------------------------*/
/* Return power domain name                                                 */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PowerDomainNameGet(uint32_t domainId, string *domainNameAddr,
    int32_t *len)
{
    int32_t status = SM_ERR_SUCCESS;
    static int32_t s_maxLen = 0;

    static string const s_name[DEV_SM_NUM_POWER] =
    {
        [DEV_SM_PD_0] = "pd0",
        [DEV_SM_PD_1] = "pd1",
        [DEV_SM_PD_2] = "pd2",
        [DEV_SM_PD_3] = "pd3",
        [DEV_SM_PD_4] = "pd4",
        [DEV_SM_PD_5] = "pd5",
        [DEV_SM_PD_6] = "pd6"
    };

    /* Get max string width */
    DEV_SM_MaxStringGet(len, &s_maxLen, s_name, DEV_SM_NUM_POWER);

    /* Check domain */
    if (DEV_SM_PdIsReserved(domainId))
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
/* Return power state name                                                  */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PowerStateNameGet(uint32_t powerState, string *stateNameAddr,
    int32_t *len)
{
    int32_t status = SM_ERR_SUCCESS;
    static int32_t s_maxLen = 0;

    static string const s_name[DEV_SM_NUM_POWER_STATE] =
    {
        [DEV_SM_POWER_STATE_OFF] = "off",
        [DEV_SM_POWER_STATE_P1] =  "p1",
        [DEV_SM_POWER_STATE_P2] =  "p2",
        [DEV_SM_POWER_STATE_ON] =  "on"
    };

    /* Get max string width */
    DEV_SM_MaxStringGet(len, &s_maxLen, s_name, DEV_SM_NUM_POWER_STATE);

    /* Check state */
    if (powerState >= DEV_SM_NUM_POWER_STATE)
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        /* Return pointer to name */
        *stateNameAddr = s_name[powerState];
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set power domain state                                                   */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PowerStateSet(uint32_t domainId, uint8_t powerState)
{
    int32_t status = SM_ERR_SUCCESS;

    if (DEV_SM_PdIsReserved(domainId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        /* Handle post power on loads */
        if ((s_powerState[domainId] == DEV_SM_POWER_STATE_OFF)
            && (powerState != DEV_SM_POWER_STATE_OFF))
        {
            status = DEV_SM_PowerUpPost(domainId);
        }

        /* Handle pre power down tasks */
        if ((s_powerState[domainId] != DEV_SM_POWER_STATE_OFF)
            && (powerState == DEV_SM_POWER_STATE_OFF))
        {
            status = DEV_SM_PowerDownPre(domainId);
        }

        s_powerState[domainId] = powerState;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get power domain state                                                   */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PowerStateGet(uint32_t domainId, uint8_t *powerState)
{
    int32_t status = SM_ERR_SUCCESS;
    *powerState = DEV_SM_POWER_STATE_OFF;

    /* Check domain */
    if (DEV_SM_PdIsReserved(domainId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        *powerState = s_powerState[domainId];
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set power domain retention mode                                          */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PowerRetModeSet(uint32_t domainId, uint32_t memRetMask)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check fuse state of power domain */
    if (DEV_SM_PdIsReserved(domainId))
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get power domain retention mask                                          */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PowerRetMaskGet(uint32_t domainId, uint32_t *retMask)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check domain */
    if (DEV_SM_PdIsReserved(domainId))
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        *retMask = 1UL << domainId;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Check if power domain is disabled in fuses                               */
/*--------------------------------------------------------------------------*/
bool DEV_SM_PdIsReserved(uint32_t domainId)
{
    bool rc = false;

    /* Check fuse state of power domain */
    if (DEV_SM_FusePdDisabled(domainId))
    {
        rc = true;
    }

    /* Return status */
    return rc;
}

