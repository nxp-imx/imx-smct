/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */


/*==========================================================================*/
/* File containing the implementation of the fuse access functions.         */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "dev_sm.h"

/* Local defines */

/* Local types */

/* Fuse map */
typedef struct
{
    uint16_t bitIdx;
    uint8_t bitWidth;
} dev_sm_fuse_map_t;

/* Local variables */

/* Fuse ID map */
/* coverity[misra_c_2012_rule_8_9_violation] */
static dev_sm_fuse_map_t s_fuseMap[DEV_SM_NUM_FUSE] =
{
    [DEV_SM_FUSE_ECID3]              = {384U,   32U},
    [DEV_SM_FUSE_ECID2]              = {416U,   32U},
    [DEV_SM_FUSE_ECID1]              = {448U,   32U},
    [DEV_SM_FUSE_ECID0]              = {480U,   32U},
    [DEV_SM_FUSE_SI_REV]             = {544U,   4U},
    [DEV_SM_FUSE_PART_NUM]           = {548U,   8U},
    [DEV_SM_FUSE_MARKET_SEGMENT]     = {556U,   2U},
    [DEV_SM_FUSE_SPEED_GRADING]      = {558U,   6U},
    [DEV_SM_FUSE_NPU_DISABLE]        = {576U,   1U},
    [DEV_SM_FUSE_A55_CORE_DISABLE]   = {577U,   4U},
    [DEV_SM_FUSE_A55_CORE0_DISABLE]  = {577U,   1U},
    [DEV_SM_FUSE_A55_CORE1_DISABLE]  = {578U,   1U},
    [DEV_SM_FUSE_A55_CORE2_DISABLE]  = {579U,   1U},
    [DEV_SM_FUSE_A55_CORE3_DISABLE]  = {580U,   1U},
    [DEV_SM_FUSE_M7_0_DISABLE]       = {585U,   1U},
    [DEV_SM_FUSE_M33_SYNC_DISABLE]   = {592U,   1U},
    [DEV_SM_FUSE_M7_1_DISABLE]       = {593U,   1U},
    [DEV_SM_FUSE_DCSS_DISABLE]       = {598U,   1U},
    [DEV_SM_FUSE_PCIE1_DISABLE]      = {614U,   1U},
    [DEV_SM_FUSE_PCIE2_DISABLE]      = {615U,   1U},
    [DEV_SM_FUSE_TSENSOR0_TRIM1]     = {1216U,  32U},
    [DEV_SM_FUSE_TSENSOR0_TRIM2]     = {1248U,  32U},
    [DEV_SM_FUSE_TSENSOR1_TRIM1]     = {1280U,  32U},
    [DEV_SM_FUSE_TSENSOR1_TRIM2]     = {1312U,  32U},
    [DEV_SM_FUSE_FRO_TRIM]           = {1344U,  18U},
    [DEV_SM_FUSE_PMRO]               = {16928U, 32U},
    [DEV_SM_FUSE_M33_ROM_PATCH_VER]  = {17152U, 32U}
};

/* Local functions */

/*--------------------------------------------------------------------------*/
/* Get address of a fuse word                                               */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_FuseInfoGet(uint32_t fuseWord, uint32_t *addr)
{
    int32_t status = SM_ERR_SUCCESS;

    if (fuseWord < DEV_SM_NUM_OTP)
    {
        *addr = FSB_BASE + 0x8000U + (fuseWord * 4U);
    }
    else
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return result */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Read a fuse field                                                        */
/*--------------------------------------------------------------------------*/
uint32_t DEV_SM_FuseGet(uint32_t fuseId)
{
    uint32_t fuse;
    uint32_t shift;
    uint32_t mask;

    /* Get fuse word */
    fuse = FSB->FUSE[s_fuseMap[fuseId].bitIdx / 32U];

    /* Calculate shift and mask */
    shift = ((uint32_t) s_fuseMap[fuseId].bitIdx) % 32U;

    /* Added to improve the test coverage */
    SM_TEST_MODE_EXEC(SM_TEST_MODE_EXEC_LVL1,
        s_fuseMap[fuseId].bitWidth = 33U);

    /* Check the mask value not exceeding the max shift value */
    if ((uint32_t) s_fuseMap[fuseId].bitWidth  <= 32U)
    {
        mask = (2UL << (((uint32_t) s_fuseMap[fuseId].bitWidth) - 1U)) - 1U;
    }
    else
    {
        /* If exceeded, wrap to max range */
        mask = 0U;
    }

    /* Return result */
    return (fuse >> shift) & mask;
}

/*--------------------------------------------------------------------------*/
/* Read speed grading                                                       */
/*--------------------------------------------------------------------------*/
uint32_t DEV_SM_FuseSpeedGet(void)
{
    uint32_t speed;
    uint32_t freq = ES_SPEED_GRADE_HZ_DEFAULT;

    /* Get speed */
    speed = DEV_SM_FuseGet(DEV_SM_FUSE_SPEED_GRADING) & 0xFU;

    /* Added to improve the test coverage */
    SM_TEST_MODE_EXEC(SM_TEST_MODE_EXEC_LVL1, speed = 1U);

    if (speed != 0U)
    {
        /* Calculate freq */
        freq = ES_SPEED_GRADE_HZ_MAX - (speed * ES_SPEED_GRADE_HZ_STEP);
    }

    /* Return frequency */
    return freq;
}

/*--------------------------------------------------------------------------*/
/* Get the fuse state of a power domain                                     */
/*--------------------------------------------------------------------------*/
bool DEV_SM_FusePdDisabled(uint32_t domainId)
{
    bool pdDisabled = false;

    static uint32_t const s_fuseId[DEV_SM_NUM_POWER] =
    {
        [DEV_SM_PD_A55C0] =   DEV_SM_FUSE_A55_CORE0_DISABLE,
        [DEV_SM_PD_A55C1] =   DEV_SM_FUSE_A55_CORE1_DISABLE,
        [DEV_SM_PD_A55C2] =   DEV_SM_FUSE_A55_CORE2_DISABLE,
        [DEV_SM_PD_A55C3] =   DEV_SM_FUSE_A55_CORE3_DISABLE,
        [DEV_SM_PD_M70]   =   DEV_SM_FUSE_M7_0_DISABLE,
        [DEV_SM_PD_M71]   =   DEV_SM_FUSE_M7_1_DISABLE
    };

    if (domainId >= DEV_SM_NUM_POWER)
    {
        pdDisabled = true;
    }
    else
    {
        if (s_fuseId[domainId] > 0U)
        {
            /* Check fuse state */
            if (DEV_SM_FuseGet(s_fuseId[domainId]) != 0U)
            {
                pdDisabled = true;
            }
        }
    }

    /* Return state */
    return pdDisabled;
}

/*--------------------------------------------------------------------------*/
/* Get the fuse state of a CPU ID                                           */
/*--------------------------------------------------------------------------*/
bool DEV_SM_FuseCpuDisabled(uint32_t cpuId)
{
    bool cpuDisabled = false;

    static uint32_t const s_fuseId[DEV_SM_NUM_CPU] =
    {
        [DEV_SM_CPU_A55C0] = DEV_SM_FUSE_A55_CORE0_DISABLE,
        [DEV_SM_CPU_A55C1] = DEV_SM_FUSE_A55_CORE1_DISABLE,
        [DEV_SM_CPU_A55C2] = DEV_SM_FUSE_A55_CORE2_DISABLE,
        [DEV_SM_CPU_A55C3] = DEV_SM_FUSE_A55_CORE3_DISABLE,
        [DEV_SM_CPU_M7P0]  = DEV_SM_FUSE_M7_0_DISABLE,
        [DEV_SM_CPU_M7P1]  = DEV_SM_FUSE_M7_1_DISABLE,
        [DEV_SM_CPU_M33S]  = DEV_SM_FUSE_M33_SYNC_DISABLE,
        [DEV_SM_CPU_A55P]  = DEV_SM_FUSE_A55_CORE0_DISABLE
    };

    if (cpuId >= DEV_SM_NUM_CPU)
    {
        cpuDisabled = true;
    }
    else
    {
        if (s_fuseId[cpuId] > 0U)
        {
            /* Check fuse state */
            if (DEV_SM_FuseGet(s_fuseId[cpuId]) != 0U)
            {
                cpuDisabled = true;
            }
        }
    }

    /* Return state */
    return cpuDisabled;
}

