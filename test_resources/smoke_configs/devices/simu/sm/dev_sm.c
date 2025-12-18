/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*==========================================================================*/
/* File containing the implementation of the device foundation functions.   */
/*==========================================================================*/

/* Includes */

#include "sm.h"
/* coverity[misra_c_2012_rule_21_5_violation] */
#include <signal.h>
/* coverity[misra_c_2012_rule_21_10_violation] */
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
#include "dev_sm.h"
#include "brd_sm.h"

/* Local defines */

/* Local types */

/* Local variables */

/* Local functions */

static void DEV_SM_Tick(union sigval timer_data);

/*--------------------------------------------------------------------------*/
/* Init device                                                              */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_Init(void)
{
    int32_t status;
    struct sigevent signalEvent = { 0 };
    timer_t timer = NULL;
    struct itimerspec timerPeriod = { 0 };
    uint32_t prot = (((uint32_t) PROT_READ)
        | ((uint32_t) PROT_WRITE));
    uint32_t flags = (((uint32_t) MAP_PRIVATE)
        | ((uint32_t) MAP_ANONYMOUS));

    /* Create a POSIX timer */
    signalEvent.sigev_notify = SIGEV_THREAD;
    signalEvent.sigev_notify_function = &DEV_SM_Tick;
    signalEvent.sigev_value.sival_ptr = NULL;
    /* coverity[misra_c_2012_rule_19_2_violation] */
    signalEvent.sigev_notify_attributes = NULL;
    (void) timer_create(CLOCK_MONOTONIC, &signalEvent, &timer);

    /* Configure timer for 1 second periodic */
    timerPeriod.it_value.tv_sec = 1;
    timerPeriod.it_value.tv_nsec = 0;
    timerPeriod.it_interval.tv_sec = 1;
    timerPeriod.it_interval.tv_nsec = 0;

    /* Start timer */
    (void) timer_settime(timer, 0, &timerPeriod, NULL);

    /* Allocate DDR */
    /* coverity[misra_c_2012_directive_4_12_violation] */
    /* coverity[misra_c_2012_rule_11_6_violation] */
    /* coverity[misra_c_2012_directive_4_6_violation] */
    (void) mmap((void*) 0x80000000U, 0x10000, (int) prot, (int) flags,
        -1, 0);

    /* Init fault handling */
    status = DEV_SM_FaultInit();

    /* Initialize sensors */
    if (status == SM_ERR_SUCCESS)
    {
        status = DEV_SM_SensorInit();
    }

    /* Configure BBM */
    if (status == SM_ERR_SUCCESS)
    {
        status = DEV_SM_BbmInit();
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Get default resource state for LM0 (SM)                                  */
/*--------------------------------------------------------------------------*/
void DEV_SM_LmmInitGet(uint32_t *numClock, const uint32_t **clockList)
{
    /* List of clocks used by SM to be kept on */
    static const uint32_t clocks[] =
    {
    };

    /* Return list */
    *numClock = ARRAY_SIZE(clocks);
    *clockList = clocks;
}

/*--------------------------------------------------------------------------*/
/* Init power domain state                                                  */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PowerUpPost(uint32_t domainId)
{
    int32_t status = SM_ERR_SUCCESS;

    switch (domainId)
    {

        case DEV_SM_PD_0:
            status = DEV_SM_Pd0ConfigLoad();
            break;
        case DEV_SM_PD_1:
            status = DEV_SM_Pd1ConfigLoad();
            break;
        case DEV_SM_PD_2:
            status = DEV_SM_Pd2ConfigLoad();
            break;
        case DEV_SM_PD_3:
            status = DEV_SM_Pd3ConfigLoad();
            break;
        case DEV_SM_PD_4:
            status = DEV_SM_Pd4ConfigLoad();
            break;
        case DEV_SM_PD_5:
            status = DEV_SM_Pd5ConfigLoad();
            break;
        case DEV_SM_PD_6:
            status = DEV_SM_Pd6ConfigLoad();
            break;
        default:
            status = SM_ERR_NOT_FOUND;
            break;
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Power domain preamble for power-down                                     */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PowerDownPre(uint32_t domainId)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Return status */
    return status;
}

/*==========================================================================*/

/*--------------------------------------------------------------------------*/
/* Timer tick                                                               */
/*--------------------------------------------------------------------------*/
/* coverity[misra_c_2012_rule_19_2_violation] */
static void DEV_SM_Tick(union sigval timer_data)
{
    /* Call system tick */
    DEV_SM_SystemTick(1000U);

    /* Call board tick */
    BRD_SM_TimerTick(1000U);

    /* Tick BBM */
    DEV_SM_BbmHandler();

    /* Tick control */
    DEV_SM_ControlHandler();

    /* Tick sensor */
    DEV_SM_SensorHandler(0U, 0U);
}

