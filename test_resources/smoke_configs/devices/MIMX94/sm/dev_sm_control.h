/*
** ###################################################################
**
**     Copyright 2025 NXP
**
**     Redistribution and use in source and binary forms, with or without modification,
**     are permitted provided that the following conditions are met:
**
**     o Redistributions of source code must retain the above copyright notice, this list
**       of conditions and the following disclaimer.
**
**     o Redistributions in binary form must reproduce the above copyright notice, this
**       list of conditions and the following disclaimer in the documentation and/or
**       other materials provided with the distribution.
**
**     o Neither the name of the copyright holder nor the names of its
**       contributors may be used to endorse or promote products derived from this
**       software without specific prior written permission.
**
**     THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
**     ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
**     WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
**     DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
**     ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
**     (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
**     LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
**     ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
**     (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
**     SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
**
**
** ###################################################################
*/

#ifndef DEV_SM_CONTROL_H
#define DEV_SM_CONTROL_H

/*==========================================================================*/
/*!
 * @addtogroup DEV_SM_MX94_CTRL
 * @{
 *
 * @file
 * @brief
 *
 * Header file containing the SM API for the device controls.
 */
/*==========================================================================*/

/* Includes */

#include "sm.h"

/* Defines */

/*! Number of device controls */
#define DEV_SM_NUM_CTRL  27UL

/*!
 * @name Device control indexes
 */
/** @{ */
#define DEV_SM_CTRL_PDM_CLK_SEL          0U   /*!< AON PDM clock sel */
#define DEV_SM_CTRL_MQS1_SETTINGS        1U   /*!< AON MQS settings */
#define DEV_SM_CTRL_MQS2_SETTINGS        2U   /*!< WAKE MQS settings */
#define DEV_SM_CTRL_SAI1_MCLK            3U   /*!< AON SAI1 MCLK */
#define DEV_SM_CTRL_SAI2_MCLK            4U   /*!< WAKE SAI2 MCLK */
#define DEV_SM_CTRL_SAI3_MCLK            5U   /*!< WAKE SAI3 MCLK */
#define DEV_SM_CTRL_SAI4_MCLK            6U   /*!< WAKE SAI4 MCLK */
#define DEV_SM_CTRL_ADC_TEST             7U   /*!< BBSM SNVS ADC enable */
#define DEV_SM_CTRL_GPT_MUX              8U   /*!< GPT mux */
#define DEV_SM_CTRL_XBAR_DIR_CTRL        9U   /*!< XBAR IO direction */
#define DEV_SM_CTRL_XBAR_TRIG_SYNC       10U  /*!< XBAR trigger sync ctrl1 */
#define DEV_SM_CTRL_ADC_TRIGGER          11U  /*!< ADC trigger */
#define DEV_SM_CTRL_HPF1_SYNC_SRC_CFG1   12U  /*!< Hiperface#1 sync src cfg#1 */
#define DEV_SM_CTRL_HPF1_SYNC_SRC_CFG2   13U  /*!< Hiperface#1 sync src cfg#2 */
#define DEV_SM_CTRL_HPF2_SYNC_SRC_CFG1   14U  /*!< Hiperface#2 sync src cfg#1 */
#define DEV_SM_CTRL_HPF2_SYNC_SRC_CFG2   15U  /*!< Hiperface#2 sync src cfg#2 */
#define DEV_SM_CTRL_HPF1_INTR_CTRL       16U  /*!< Hiperface#1 interrupt ctrl */
#define DEV_SM_CTRL_HPF2_INTR_CTRL       17U  /*!< Hiperface#2 interrupt ctrl */
#define DEV_SM_CTRL_ENDAT3_STATUS        18U  /*!< EnDat 3.0 status register */
#define DEV_SM_CTRL_ENC_DIAG_MUX_SEL     19U  /*!< Diagnostic bus mux sel reg */
#define DEV_SM_CTRL_HPF_SYNC_OUT_CTL     20U  /*!< Hiperface ext sync out ctrl */
#define DEV_SM_CTRL_ENDAT_STRETCH_CTRL   21U  /*!< ENDAT_STRETCHER_CTRL */
#define DEV_SM_CTRL_BISS1_PULSE_STR_CTL  22U  /*!< BISS#1 pulse stretch ctrl */
#define DEV_SM_CTRL_XBAR_TRIG_SYNC_2     23U  /*!< XBAR trigger sync ctrl#2  */
#define DEV_SM_CTRL_XBAR_TRIG_SYNC_3     24U  /*!< XBAR trigger sync ctrl#3  */
#define DEV_SM_CTRL_XBAR_TRIG_SYNC_4     25U  /*!< XBAR trigger sync ctrl#4  */
#define DEV_SM_CTRL_XBAR_DIR_CTRL_2      26U   /*!< XBAR IO direction ctrl#2 */
/** @} */

/* Types */

/* Functions */

/** @} */

/* Include SM device API */

/* coverity[misra_c_2012_rule_20_1_violation] */
#include "dev_sm_control_api.h"

#endif /* DEV_SM_CONTROL_H */

