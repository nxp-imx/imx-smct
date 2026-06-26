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

#ifndef DEV_SM_RST_H
#define DEV_SM_RST_H

/*==========================================================================*/
/*!
 * @addtogroup DEV_SM_MX94_RESET
 * @{
 *
 * @file
 * @brief
 *
 * Header file containing the SM API for the device reset domains.
 */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "fsl_reset.h"

/* Defines */

/*! Number of device reset domains */
#define DEV_SM_NUM_RESET  RST_NUM_LINE

/*!
 * @name Device reset domain indexes
 */
/** @{ */
#define DEV_SM_RST_A55C0_NCPUPORESET   RST_LINE_A55C0_NCPUPORESET   /*!< 0: A55C0 NCPUPORESET */
#define DEV_SM_RST_A55C0_NCORERESET    RST_LINE_A55C0_NCORERESET    /*!< 1: A55C0 NCORERESET */
#define DEV_SM_RST_A55C1_NCPUPORESET   RST_LINE_A55C1_NCPUPORESET   /*!< 2: A55C1 NCPUPORESET */
#define DEV_SM_RST_A55C1_NCORERESET    RST_LINE_A55C1_NCORERESET    /*!< 3: A55C1 NCORERESET */
#define DEV_SM_RST_A55C2_NCPUPORESET   RST_LINE_A55C2_NCPUPORESET   /*!< 4: A55C2 NCPUPORESET */
#define DEV_SM_RST_A55C2_NCORERESET    RST_LINE_A55C2_NCORERESET    /*!< 5: A55C2 NCORERESET */
#define DEV_SM_RST_A55C3_NCPUPORESET   RST_LINE_A55C3_NCPUPORESET   /*!< 6: A55C3 NCPUPORESET */
#define DEV_SM_RST_A55C3_NCORERESET    RST_LINE_A55C3_NCORERESET    /*!< 7: A55C3 NCORERESET */
#define DEV_SM_RST_A55P_NPRESET        RST_LINE_A55P_NPRESET        /*!< 8: A55P NPRESET */
#define DEV_SM_RST_A55P_NSPORESET      RST_LINE_A55P_NSPORESET      /*!< 9: A55P NSPORESET */
#define DEV_SM_RST_A55P_NSRESET        RST_LINE_A55P_NSRESET        /*!< 10: A55P NSRESET */
#define DEV_SM_RST_A55P_NATRESET       RST_LINE_A55P_NATRESET       /*!< 11: A55P NATRESET */
#define DEV_SM_RST_A55P_NGICRESET      RST_LINE_A55P_NGICRESET      /*!< 12: A55P NGICRESET */
#define DEV_SM_RST_A55P_NPERIPHRESET   RST_LINE_A55P_NPERIPHRESET   /*!< 13: A55P NPERIPHRESET */
#define DEV_SM_RST_DDRPHY_PRESETN      RST_LINE_DDRPHY_PRESETN      /*!< 14: DDRPHY PRESETN */
#define DEV_SM_RST_DDRPHY_RESETN       RST_LINE_DDRPHY_RESETN       /*!< 15: DDRPHY RESETN */
#define DEV_SM_RST_DISP0_RESETN        RST_LINE_DISP0_RESETN        /*!< 16: DISP0 RESETN */
#define DEV_SM_RST_DISP1_RESETN        RST_LINE_DISP1_RESETN        /*!< 17: DISP1 RESETN */
#define DEV_SM_RST_LVDS_RESETN         RST_LINE_LVDS_RESETN         /*!< 18: LVDS RESETN */
#define DEV_SM_RST_USB1PHY_RESETN      RST_LINE_USB1PHY_RESETN      /*!< 19: USB1PHY RESETN */
#define DEV_SM_RST_USB2PHY_RESETN      RST_LINE_USB2PHY_RESETN      /*!< 20: USB2PHY RESETN */
#define DEV_SM_RST_PCIE1PHY_RESETN     RST_LINE_PCIE1PHY_RESETN     /*!< 21: PCIE1PHY RESETN */
#define DEV_SM_RST_PCIE2PHY_RESETN     RST_LINE_PCIE2PHY_RESETN     /*!< 22: PCIE2PHY RESETN */
#define DEV_SM_RST_ENETPHY_PCS_RESETN  RST_LINE_ENETPHY_PCS_RESETN  /*!< 23: ENETPHY PCS RESETN */
#define DEV_SM_RST_ECAT_IP_RESETN      RST_LINE_ECAT_IP_RESETN      /*!< 24: ECAT IP RESETN */
#define DEV_SM_RST_V2X_RESETB          RST_LINE_V2X_RESETB          /*!< 25: V2X RESETB */
#define DEV_SM_RST_BISS_RESETN         RST_LINE_BISS_RESETN         /*!< 26: BISS RESETN */
#define DEV_SM_RST_ENDAT3_RESETN       RST_LINE_ENDAT3_RESETN       /*!< 27: ENDAT3 RESETN */
#define DEV_SM_RST_ENDAT2_RESETN       RST_LINE_ENDAT2_RESETN       /*!< 28: ENDAT2 RESETN */
#define DEV_SM_RST_HIPERFACE_RESETN    RST_LINE_HIPERFACE_RESETN    /*!< 29: HIPERFACE RESETN */
#define DEV_SM_RST_ANAMIX              RST_LINE_ANAMIX              /*!< 30: ANAMIX */
#define DEV_SM_RST_AONMIX_TOP          RST_LINE_AONMIX_TOP          /*!< 31: AONMIX TOP */
#define DEV_SM_RST_AONMIX_M33          RST_LINE_AONMIX_M33          /*!< 32: AONMIX M33 */
#define DEV_SM_RST_AONMIX_ELE          RST_LINE_AONMIX_ELE          /*!< 33: AONMIX ELE */
#define DEV_SM_RST_BBSMMIX             RST_LINE_BBSMMIX             /*!< 34: BBSMMIX */
#define DEV_SM_RST_M71MIX              RST_LINE_M71MIX              /*!< 35: M71MIX */
#define DEV_SM_RST_CCMSRCGPCMIX        RST_LINE_CCMSRCGPCMIX        /*!< 36: CCMSRCGPCMIX */
#define DEV_SM_RST_CORTEXAMIX_CORE0    RST_LINE_CORTEXAMIX_CORE0    /*!< 37: CORTEXAMIX CORE0 */
#define DEV_SM_RST_CORTEXAMIX_CORE1    RST_LINE_CORTEXAMIX_CORE1    /*!< 38: CORTEXAMIX CORE1 */
#define DEV_SM_RST_CORTEXAMIX_CORE2    RST_LINE_CORTEXAMIX_CORE2    /*!< 39: CORTEXAMIX CORE2 */
#define DEV_SM_RST_CORTEXAMIX_CORE3    RST_LINE_CORTEXAMIX_CORE3    /*!< 40: CORTEXAMIX CORE3 */
#define DEV_SM_RST_CORTEXAMIX_PLATFORM RST_LINE_CORTEXAMIX_PLATFORM /*!< 41: CORTEXAMIX PLATFORM */
#define DEV_SM_RST_DDRMIX_TOP          RST_LINE_DDRMIX_TOP          /*!< 42: DDRMIX TOP */
#define DEV_SM_RST_DDRMIX_PHY          RST_LINE_DDRMIX_PHY          /*!< 43: DDRMIX PHY */
#define DEV_SM_RST_DISPLAYMIX          RST_LINE_DISPLAYMIX          /*!< 44: DISPLAYMIX */
#define DEV_SM_RST_M70MIX              RST_LINE_M70MIX              /*!< 45: M70MIX */
#define DEV_SM_RST_HSIOMIX_TOP         RST_LINE_HSIOMIX_TOP         /*!< 46: HSIOMIX TOP */
#define DEV_SM_RST_HSIOMIX_WAON        RST_LINE_HSIOMIX_WAON        /*!< 47: HSIOMIX WAON */
#define DEV_SM_RST_NETCMIX             RST_LINE_NETCMIX             /*!< 48: NETCMIX */
#define DEV_SM_RST_NETCMIX_M33         RST_LINE_NETCMIX_M33         /*!< 49: NETCMIX M33 */
#define DEV_SM_RST_NETCMIX_WDOG_7_8    RST_LINE_NETCMIX_WDOG_7_8    /*!< 50: NETCMIX WDOG 7-8 */
#define DEV_SM_RST_NOCMIX              RST_LINE_NOCMIX              /*!< 51: NOCMIX */
#define DEV_SM_RST_NOCMIX_WDOG_3_4     RST_LINE_NOCMIX_WDOG_3_4     /*!< 52: NOCMIX WDOG 3-4 */
#define DEV_SM_RST_NPUMIX              RST_LINE_NPUMIX              /*!< 53: NPUMIX */
#define DEV_SM_RST_WAKEUPMIX_TOP       RST_LINE_WAKEUPMIX_TOP       /*!< 54: WAKEUPMIX TOP */
#define DEV_SM_RST_WAKEUPMIX_JTAG      RST_LINE_WAKEUPMIX_JTAG      /*!< 55: WAKEUPMIX JTAG */
#define DEV_SM_RST_WAKEUPMIX_WDOG_5    RST_LINE_WAKEUPMIX_WDOG_5    /*!< 56: WAKEUPMIX WDOG 5 */
#define DEV_SM_RST_WAKEUPMIX_WDOG_6    RST_LINE_WAKEUPMIX_WDOG_6    /*!< 57: WAKEUPMIX WDOG 6 */
/** @} */

/*!
 * @name Device reset domain states
 */
/** @{ */
#define DEV_SM_RST_COLD  0U  /*!< Cold reset - no retention */
/** @} */

/* Types */

/* Functions */

/** @} */

/* Include SM device API */

/* coverity[misra_c_2012_rule_20_1_violation] */
#include "dev_sm_reset_api.h"

#endif /* DEV_SM_RST_H */

