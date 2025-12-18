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

#ifndef DEV_SM_PERF_H
#define DEV_SM_PERF_H

/*==========================================================================*/
/*!
 * @addtogroup DEV_SM_MX94_PERF
 * @{
 *
 * @file
 * @brief
 *
 * Header file containing the SM API for the device performance domains.
 */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "fsl_supply.h"

/* Defines */

/*! Number of device performance domains */
#define DEV_SM_NUM_PERF     11U

/*!
 * @name Device performance domain indexes
 */
/** @{ */
#define DEV_SM_PERF_M33     0U   /*!< M33 domain */
#define DEV_SM_PERF_M33S    1U   /*!< M33_S domain */
#define DEV_SM_PERF_WAKEUP  2U   /*!< WAKEUP domain */
#define DEV_SM_PERF_M70     3U   /*!< M7_0 domain */
#define DEV_SM_PERF_M71     4U   /*!< M7_1 domain */
#define DEV_SM_PERF_DRAM    5U   /*!< DRAM domain */
#define DEV_SM_PERF_HSIO    6U   /*!< HSIO domain */
#define DEV_SM_PERF_NPU     7U   /*!< NPU domain */
#define DEV_SM_PERF_NOC     8U   /*!< NOC domain */
#define DEV_SM_PERF_A55     9U   /*!< A55 domain */
#define DEV_SM_PERF_DISP    10U   /*!< DISP domain */
/** @} */

/*!
 * @name Device performance domain levels
 */
/** @{ */
#define DEV_SM_PERF_LVL_PRK  0U  /*!< Default/reset drive */
#define DEV_SM_PERF_LVL_LOW  1U  /*!< Low drive per datasheet */
#define DEV_SM_PERF_LVL_NOM  2U  /*!< Nominal drive per datasheet */
#define DEV_SM_PERF_LVL_ODV  3U  /*!< Overdrive per datasheet */
/** @} */

/* Types */

/* Functions */

/** @} */

/* Include SM device API */

/* coverity[misra_c_2012_rule_20_1_violation] */
#include "dev_sm_perf_api.h"

#endif /* DEV_SM_PERF_H */

