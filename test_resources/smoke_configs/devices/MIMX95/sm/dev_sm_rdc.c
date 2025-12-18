/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

/*==========================================================================*/
/* File containing the implementation of the device RDC functions.          */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "dev_sm.h"
#include "fsl_ele.h"
#include "fsl_device_registers.h"
#include "config_trdc.h"

/* Local defines */

/* DDR MRC region start address (inclusive) */
#define DDR_MRC_REGION_START  0x4902A040U

/* DDR MRC region end address (inclusive) */
#define DDR_MRC_REGION_END    0x4902AFC0U

/* Local types */

typedef struct
{
    string name;
    uint32_t rdcBase;
    char rdcLabel;
    uint8_t apiId;
    const uint32_t *config;
    uint32_t pd;
} dev_sm_trdc_info_t;

/* Local variables */

static const uint32_t s_trdcAon[] = SM_TRDC_A_CONFIG;
static const uint32_t s_trdcCamera[] = SM_TRDC_C_CONFIG;
static const uint32_t s_trdcDisplay[] = SM_TRDC_D_CONFIG;
static const uint32_t s_trdcNetc[] = SM_TRDC_E_CONFIG;
static const uint32_t s_trdcGpu[] = SM_TRDC_G_CONFIG;
static const uint32_t s_trdcHsio[] = SM_TRDC_H_CONFIG;
static const uint32_t s_trdcMega[] = SM_TRDC_M_CONFIG;
static const uint32_t s_trdcNoc[] = SM_TRDC_N_CONFIG;
static const uint32_t s_trdcVpu[] = SM_TRDC_V_CONFIG;
static const uint32_t s_trdcWakeup[] = SM_TRDC_W_CONFIG;

static const dev_sm_trdc_info_t s_trdcInfo[DEV_SM_NUM_RDC] =
{
    {"aon",    0x44270000, 'A', 0x74U, s_trdcAon,     DEV_SM_PD_AON},
    {"mega",   0x42810000, 'M', 0x82U, s_trdcMega,    DEV_SM_PD_WAKEUP},
    {"wakeup", 0x42460000, 'W', 0x78U, s_trdcWakeup,  DEV_SM_PD_WAKEUP},
    {"camera", 0x4AC40000, 'C', 0x92U, s_trdcCamera,  DEV_SM_PD_CAMERA},
    {"hsio",   0x4C040000, 'H', 0x95U, s_trdcHsio,    DEV_SM_PD_HSIO_TOP},
    {"noc",    0x49010000, 'N', 0x86U, s_trdcNoc,     DEV_SM_PD_NOC},
    {"disp",   0x4B040000, 'D', 0xDEU, s_trdcDisplay, DEV_SM_PD_DISPLAY},
    {"netc",   0x4C840000, 'E', 0xB9U, s_trdcNetc,    DEV_SM_PD_NETC},
    {"gpu",    0x4D840000, 'G', 0x65U, s_trdcGpu,     DEV_SM_PD_GPU},
    {"vpu",    0x4C440000, 'V', 0xF1U, s_trdcVpu,     DEV_SM_PD_VPU}
};

/*--------------------------------------------------------------------------*/
/* Init RDC                                                                 */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_RdcInit(void)
{
    int32_t status = SM_ERR_SUCCESS;

    /* RDC Init */
    for (uint32_t rdcId = 0U; rdcId < DEV_SM_NUM_RDC; rdcId++)
    {
        /* Skip if no ID */
        if (s_trdcInfo[rdcId].apiId == 0U)
        {
            continue;
        }

#ifdef DEVICE_HAS_ELE
        /* Request RDC from ELE */
        ELE_RdcRelease(s_trdcInfo[rdcId].apiId);

        /* Check ELE error */
        if (g_eleStatus != SM_ERR_SUCCESS)
        {
            status = g_eleStatus;
            break;
        }
#endif
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Return RDC name and address                                              */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_RdcInfoGet(uint32_t rdcId, string *rdcNameAddr,
    char *rdcLabel, uint32_t *rdcBase)
{
    int32_t status = SM_ERR_SUCCESS;

    /* Check if invalid */
    if (rdcId >= DEV_SM_NUM_RDC)
    {
        status = SM_ERR_NOT_FOUND;
    }

    /* Return results */
    if (status == SM_ERR_SUCCESS)
    {
        if (rdcNameAddr != NULL)
        {
            /* Return pointer to name */
            *rdcNameAddr = s_trdcInfo[rdcId].name;
        }

        if (rdcBase != NULL)
        {
            /* Return address of RDC */
            *rdcBase = s_trdcInfo[rdcId].rdcBase;
        }

        if (rdcLabel != NULL)
        {
            /* Return label */
            *rdcLabel = s_trdcInfo[rdcId].rdcLabel;
        }

        /* Check if powered */
        if (!SRC_MixIsPwrSwitchOn(s_trdcInfo[rdcId].pd))
        {
            status = SM_ERR_POWER;
        }
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Load RDC config                                                          */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_RdcLoad(uint32_t rdcId)
{
    int32_t status = SM_ERR_NOT_FOUND;

    /* Check ID */
    if (rdcId < DEV_SM_NUM_RDC)
    {
        /* Load config */
        status = CONFIG_Load((uint32_t*)
            s_trdcInfo[rdcId].rdcBase, s_trdcInfo[rdcId].config);
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Load RDC config                                                          */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_RdcDdrBlock(bool enable)
{
    int32_t status;
    uint32_t rdcId = DEV_SM_TRDC_N;

    /* Load config */
    status = CONFIG_LoadRange((uint32_t*)
        s_trdcInfo[rdcId].rdcBase, s_trdcInfo[rdcId].config,
        true, DDR_MRC_REGION_START, DDR_MRC_REGION_END, enable);

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set RDC device access rights                                             */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_RdcAccessSet(uint32_t deviceId, bool allow, uint8_t domId,
    bool secure)
{
    /* Return status */
    return SM_ERR_NOT_SUPPORTED;
}

