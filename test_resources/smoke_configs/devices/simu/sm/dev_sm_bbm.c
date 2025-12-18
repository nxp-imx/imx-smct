/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*==========================================================================*/
/* File containing the implementation of the device battery-backed module.  */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "dev_sm.h"
#include "lmm.h"

/* Local defines */

/* Local types */

/* Local variables */

static uint32_t s_bbmGpr[DEV_SM_NUM_GPR];
static uint64_t s_ticks = 0ULL;
static uint64_t s_alarm = 0ULL;
static bool s_alarmEnable = false;
static bool s_rolloverEnable = false;
static bool s_button = false;

/*--------------------------------------------------------------------------*/
/* Init BBM                                                                 */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmInit(void)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Return BBM status found at boot                                          */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmGetBootStatus(uint32_t *flags)
{
    int32_t status = SM_ERR_SUCCESS;

    /* No conditions */
    *flags = 0U;

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set BBM GPR                                                              */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmGprSet(uint32_t index, uint32_t value)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check GPR */
    if (index < DEV_SM_NUM_GPR)
    {
        s_bbmGpr[index] = value;
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get BBM GPR                                                              */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmGprGet(uint32_t index, uint32_t *value)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check GPR */
    if (index < DEV_SM_NUM_GPR)
    {
        *value = s_bbmGpr[index];
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Return RTC name                                                          */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmRtcNameGet(uint32_t rtcId, string *rtcNameAddr,
    int32_t *len)
{
    int32_t status = SM_ERR_SUCCESS;
    static int32_t s_maxLen = 0;

    static string const s_name[DEV_SM_NUM_RTC] =
    {
        [DEV_SM_RTC_BBNSM] = "bbnsm"
    };

    /* Get max string width */
    DEV_SM_MaxStringGet(len, &s_maxLen, s_name, DEV_SM_NUM_RTC);

    /* Check RTC */
    if (rtcId >= DEV_SM_NUM_RTC)
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        /* Return pointer to name */
        *rtcNameAddr = s_name[rtcId];
    }

    SM_TEST_MODE_ERR(SM_TEST_MODE_DEV_LVL1, SM_ERR_TEST)

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Return RTC info                                                          */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmRtcDescribe(uint32_t rtcId, uint32_t *secWidth,
    uint32_t *tickWidth, uint32_t *ticksPerSec)
{
    /* Return RTC info */
    *secWidth = 32U;
    *tickWidth = 47U;
    *ticksPerSec = 32768U;

    /* Return status */
    return SM_ERR_SUCCESS;
}

/*--------------------------------------------------------------------------*/
/* Set BBM RTC time                                                         */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmRtcTimeSet(uint32_t rtcId, uint64_t val, bool ticks)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check time format */
    if (ticks)
    {
        /* Get ticks */
        s_ticks = val;
    }
    else
    {
        /* Get seconds */
        s_ticks = val << 15U;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get BBM RTC time                                                         */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmRtcTimeGet(uint32_t rtcId, uint64_t *val, bool ticks)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check time format */
    if (ticks)
    {
        /* Get ticks */
        *val = s_ticks;
    }
    else
    {
        /* Get seconds */
        *val = s_ticks >> 15U;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get BBM RTC state                                                        */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmRtcStateGet(uint32_t rtcId, uint32_t *state)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Default state */
    *state = 0U;

    SM_TEST_MODE_ERR(SM_TEST_MODE_DEV_LVL2, SM_ERR_TEST)

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set BBM RTC alarm                                                        */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmRtcAlarmSet(uint32_t rtcId, bool enable, uint64_t val)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Enable? */
    if (enable)
    {
        uint64_t ticks = val << 15U;

        /* Check if valid time */
        if (ticks <= s_ticks)
        {
            status = SM_ERR_INVALID_PARAMETERS;
        }
        else
        {
            /* Save alarm */
            s_alarm = ticks;

            /* Enable */
            s_alarmEnable = true;
        }
    }
    else
    {
        /* Disable alarm interrupt */
        s_alarmEnable = false;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Enable BBM RTC rollover interrupt                                        */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmRtcRollover(uint32_t rtcId)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Enable */
    s_rolloverEnable = true;

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set Get BBM button state                                                 */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_BbmButtonGet(bool *buttonAsserted)
{
    int32_t status = SM_ERR_SUCCESS;

    *buttonAsserted = s_button;

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Tick handler (one second)                                                */
/*--------------------------------------------------------------------------*/
void DEV_SM_BbmHandler(void)
{
    /* Increment time by 1 second */
    /*
     * False Positive: Roll over condition is taken case below
     */
    /* coverity[cert_int30_c_violation:FALSE] */
    s_ticks += (1ULL << 15U);

    /* Roll over */
    if (s_ticks > (0xFFFFFFFFULL << 15U))
    {
        s_ticks = 0ULL;

        /* Check rollover */
        if (s_rolloverEnable)
        {
            s_rolloverEnable = false;
            LMM_BbmRtcRolloverEvent(DEV_SM_RTC_BBNSM);
        }
    }

    /* Check alarm */
    if (s_alarmEnable && (s_ticks >= s_alarm))
    {
        LMM_BbmRtcAlarmEvent(DEV_SM_RTC_BBNSM);
    }

    /* Toggle button */
    s_button = !s_button;
    if (s_button)
    {
        LMM_BbmButtonEvent();
    }
}

