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

#ifndef DEV_SM_PIN_H
#define DEV_SM_PIN_H

/*==========================================================================*/
/*!
 * @addtogroup DEV_SM_MX94_PIN
 * @{
 *
 * @file
 * @brief
 *
 * Header file containing the SM API for the device pins.
 */
/*==========================================================================*/

/* Includes */

#include "sm.h"

/* Defines */

/*! Number of device pin */
#define DEV_SM_NUM_PIN    193U

/*! Number of device daisy */
#define DEV_SM_NUM_DAISY  205U

/*!
 * @name Device pin indexes
 *
 * See the IOMUXC register list in the i.MX95 RM.
 */
/** @{ */
#define DEV_SM_PIN_DAP_TDI                    0U    /*!< DAP TDI pin */
#define DEV_SM_PIN_DAP_TMS_SWDIO              1U    /*!< DAP TMS SWDIO pin */
#define DEV_SM_PIN_DAP_TCLK_SWCLK             2U    /*!< DAP TCLK SWCLK pin */
#define DEV_SM_PIN_DAP_TDO_TRACESWO           3U    /*!< DAP TDO TRACESWO pin */
#define DEV_SM_PIN_GPIO_IO00                  4U    /*!< GPIO IO00 pin */
#define DEV_SM_PIN_GPIO_IO01                  5U    /*!< GPIO IO01 pin */
#define DEV_SM_PIN_GPIO_IO02                  6U    /*!< GPIO IO02 pin */
#define DEV_SM_PIN_GPIO_IO03                  7U    /*!< GPIO IO03 pin */
#define DEV_SM_PIN_GPIO_IO04                  8U    /*!< GPIO IO04 pin */
#define DEV_SM_PIN_GPIO_IO05                  9U    /*!< GPIO IO05 pin */
#define DEV_SM_PIN_GPIO_IO06                  10U   /*!< GPIO IO06 pin */
#define DEV_SM_PIN_GPIO_IO07                  11U   /*!< GPIO IO07 pin */
#define DEV_SM_PIN_GPIO_IO08                  12U   /*!< GPIO IO08 pin */
#define DEV_SM_PIN_GPIO_IO09                  13U   /*!< GPIO IO09 pin */
#define DEV_SM_PIN_GPIO_IO10                  14U   /*!< GPIO IO10 pin */
#define DEV_SM_PIN_GPIO_IO11                  15U   /*!< GPIO IO11 pin */
#define DEV_SM_PIN_GPIO_IO12                  16U   /*!< GPIO IO12 pin */
#define DEV_SM_PIN_GPIO_IO13                  17U   /*!< GPIO IO13 pin */
#define DEV_SM_PIN_GPIO_IO14                  18U   /*!< GPIO IO14 pin */
#define DEV_SM_PIN_GPIO_IO15                  19U   /*!< GPIO IO15 pin */
#define DEV_SM_PIN_GPIO_IO16                  20U   /*!< GPIO IO16 pin */
#define DEV_SM_PIN_GPIO_IO17                  21U   /*!< GPIO IO17 pin */
#define DEV_SM_PIN_GPIO_IO18                  22U   /*!< GPIO IO18 pin */
#define DEV_SM_PIN_GPIO_IO19                  23U   /*!< GPIO IO19 pin */
#define DEV_SM_PIN_GPIO_IO20                  24U   /*!< GPIO IO20 pin */
#define DEV_SM_PIN_GPIO_IO21                  25U   /*!< GPIO IO21 pin */
#define DEV_SM_PIN_GPIO_IO22                  26U   /*!< GPIO IO22 pin */
#define DEV_SM_PIN_GPIO_IO23                  27U   /*!< GPIO IO23 pin */
#define DEV_SM_PIN_GPIO_IO24                  28U   /*!< GPIO IO24 pin */
#define DEV_SM_PIN_GPIO_IO25                  29U   /*!< GPIO IO25 pin */
#define DEV_SM_PIN_GPIO_IO26                  30U   /*!< GPIO IO26 pin */
#define DEV_SM_PIN_GPIO_IO27                  31U   /*!< GPIO IO27 pin */
#define DEV_SM_PIN_GPIO_IO28                  32U   /*!< GPIO IO28 pin */
#define DEV_SM_PIN_GPIO_IO29                  33U   /*!< GPIO IO29 pin */
#define DEV_SM_PIN_GPIO_IO30                  34U   /*!< GPIO IO30 pin */
#define DEV_SM_PIN_GPIO_IO31                  35U   /*!< GPIO IO31 pin */
#define DEV_SM_PIN_GPIO_IO32                  36U   /*!< GPIO IO32 pin */
#define DEV_SM_PIN_GPIO_IO33                  37U   /*!< GPIO IO33 pin */
#define DEV_SM_PIN_GPIO_IO34                  38U   /*!< GPIO IO34 pin */
#define DEV_SM_PIN_GPIO_IO35                  39U   /*!< GPIO IO35 pin */
#define DEV_SM_PIN_GPIO_IO36                  40U   /*!< GPIO IO36 pin */
#define DEV_SM_PIN_GPIO_IO37                  41U   /*!< GPIO IO37 pin */
#define DEV_SM_PIN_GPIO_IO38                  42U   /*!< GPIO IO38 pin */
#define DEV_SM_PIN_GPIO_IO39                  43U   /*!< GPIO IO39 pin */
#define DEV_SM_PIN_GPIO_IO40                  44U   /*!< GPIO IO40 pin */
#define DEV_SM_PIN_GPIO_IO41                  45U   /*!< GPIO IO41 pin */
#define DEV_SM_PIN_GPIO_IO42                  46U   /*!< GPIO IO42 pin */
#define DEV_SM_PIN_GPIO_IO43                  47U   /*!< GPIO IO43 pin */
#define DEV_SM_PIN_GPIO_IO44                  48U   /*!< GPIO IO44 pin */
#define DEV_SM_PIN_GPIO_IO45                  49U   /*!< GPIO IO45 pin */
#define DEV_SM_PIN_GPIO_IO46                  50U   /*!< GPIO IO46 pin */
#define DEV_SM_PIN_GPIO_IO47                  51U   /*!< GPIO IO47 pin */
#define DEV_SM_PIN_GPIO_IO48                  52U   /*!< GPIO IO48 pin */
#define DEV_SM_PIN_GPIO_IO49                  53U   /*!< GPIO IO49 pin */
#define DEV_SM_PIN_GPIO_IO50                  54U   /*!< GPIO IO50 pin */
#define DEV_SM_PIN_GPIO_IO51                  55U   /*!< GPIO IO51 pin */
#define DEV_SM_PIN_GPIO_IO52                  56U   /*!< GPIO IO52 pin */
#define DEV_SM_PIN_GPIO_IO53                  57U   /*!< GPIO IO53 pin */
#define DEV_SM_PIN_GPIO_IO54                  58U   /*!< GPIO IO54 pin */
#define DEV_SM_PIN_GPIO_IO55                  59U   /*!< GPIO IO55 pin */
#define DEV_SM_PIN_GPIO_IO56                  60U   /*!< GPIO IO56 pin */
#define DEV_SM_PIN_GPIO_IO57                  61U   /*!< GPIO IO57 pin */
#define DEV_SM_PIN_CCM_CLKO1                  62U   /*!< CCM CLKO1 pin */
#define DEV_SM_PIN_CCM_CLKO2                  63U   /*!< CCM CLKO2 pin */
#define DEV_SM_PIN_CCM_CLKO3                  64U   /*!< CCM CLKO3 pin */
#define DEV_SM_PIN_CCM_CLKO4                  65U   /*!< CCM CLKO4 pin */
#define DEV_SM_PIN_ETH2_MDC_GPIO1             66U   /*!< ETH2 MDC GPIO1 pin */
#define DEV_SM_PIN_ETH2_MDIO_GPIO2            67U   /*!< ETH2 MDIO GPIO2 pin */
#define DEV_SM_PIN_ETH2_TXD3                  68U   /*!< ETH2 TXD3 pin */
#define DEV_SM_PIN_ETH2_TXD2                  69U   /*!< ETH2 TXD2 pin */
#define DEV_SM_PIN_ETH2_TXD1                  70U   /*!< ETH2 TXD1 pin */
#define DEV_SM_PIN_ETH2_TXD0                  71U   /*!< ETH2 TXD0 pin */
#define DEV_SM_PIN_ETH2_TX_CTL                72U   /*!< ETH2 TX CTL pin */
#define DEV_SM_PIN_ETH2_TX_CLK                73U   /*!< ETH2 TX CLK pin */
#define DEV_SM_PIN_ETH2_RX_CTL                74U   /*!< ETH2 RX CTL pin */
#define DEV_SM_PIN_ETH2_RX_CLK                75U   /*!< ETH2 RX CLK pin */
#define DEV_SM_PIN_ETH2_RXD0                  76U   /*!< ETH2 RXD0 pin */
#define DEV_SM_PIN_ETH2_RXD1                  77U   /*!< ETH2 RXD1 pin */
#define DEV_SM_PIN_ETH2_RXD2                  78U   /*!< ETH2 RXD2 pin */
#define DEV_SM_PIN_ETH2_RXD3                  79U   /*!< ETH2 RXD3 pin */
#define DEV_SM_PIN_ETH3_MDC_GPIO1             80U   /*!< ETH3 MDC GPIO1 pin */
#define DEV_SM_PIN_ETH3_MDIO_GPIO2            81U   /*!< ETH3 MDIO GPIO2 pin */
#define DEV_SM_PIN_ETH3_TXD3                  82U   /*!< ETH3 TXD3 pin */
#define DEV_SM_PIN_ETH3_TXD2                  83U   /*!< ETH3 TXD2 pin */
#define DEV_SM_PIN_ETH3_TXD1                  84U   /*!< ETH3 TXD1 pin */
#define DEV_SM_PIN_ETH3_TXD0                  85U   /*!< ETH3 TXD0 pin */
#define DEV_SM_PIN_ETH3_TX_CTL                86U   /*!< ETH3 TX CTL pin */
#define DEV_SM_PIN_ETH3_TX_CLK                87U   /*!< ETH3 TX CLK pin */
#define DEV_SM_PIN_ETH3_RX_CTL                88U   /*!< ETH3 RX CTL pin */
#define DEV_SM_PIN_ETH3_RX_CLK                89U   /*!< ETH3 RX CLK pin */
#define DEV_SM_PIN_ETH3_RXD0                  90U   /*!< ETH3 RXD0 pin */
#define DEV_SM_PIN_ETH3_RXD1                  91U   /*!< ETH3 RXD1 pin */
#define DEV_SM_PIN_ETH3_RXD2                  92U   /*!< ETH3 RXD2 pin */
#define DEV_SM_PIN_ETH3_RXD3                  93U   /*!< ETH3 RXD3 pin */
#define DEV_SM_PIN_ETH4_MDC_GPIO1             94U   /*!< ETH4 MDC GPIO1 pin */
#define DEV_SM_PIN_ETH4_MDIO_GPIO2            95U   /*!< ETH4 MDIO GPIO2 pin */
#define DEV_SM_PIN_ETH4_TX_CLK                96U   /*!< ETH4 TX CLK pin */
#define DEV_SM_PIN_ETH4_TX_CTL                97U   /*!< ETH4 TX CTL pin */
#define DEV_SM_PIN_ETH4_TXD0                  98U   /*!< ETH4 TXD0 pin */
#define DEV_SM_PIN_ETH4_TXD1                  99U   /*!< ETH4 TXD1 pin */
#define DEV_SM_PIN_ETH4_TXD2                  100U  /*!< ETH4 TXD2 pin */
#define DEV_SM_PIN_ETH4_TXD3                  101U  /*!< ETH4 TXD3 pin */
#define DEV_SM_PIN_ETH4_RXD0                  102U  /*!< ETH4 RXD0 pin */
#define DEV_SM_PIN_ETH4_RXD1                  103U  /*!< ETH4 RXD1 pin */
#define DEV_SM_PIN_ETH4_RXD2                  104U  /*!< ETH4 RXD2 pin */
#define DEV_SM_PIN_ETH4_RXD3                  105U  /*!< ETH4 RXD3 pin */
#define DEV_SM_PIN_ETH4_RX_CTL                106U  /*!< ETH4 RX CTL pin */
#define DEV_SM_PIN_ETH4_RX_CLK                107U  /*!< ETH4 RX CLK pin */
#define DEV_SM_PIN_ETH0_TXD0                  108U  /*!< ETH0 TXD0 pin */
#define DEV_SM_PIN_ETH0_TXD1                  109U  /*!< ETH0 TXD1 pin */
#define DEV_SM_PIN_ETH0_TX_EN                 110U  /*!< ETH0 TX EN pin */
#define DEV_SM_PIN_ETH0_TX_CLK                111U  /*!< ETH0 TX CLK pin */
#define DEV_SM_PIN_ETH0_RXD0                  112U  /*!< ETH0 RXD0 pin */
#define DEV_SM_PIN_ETH0_RXD1                  113U  /*!< ETH0 RXD1 pin */
#define DEV_SM_PIN_ETH0_RX_DV                 114U  /*!< ETH0 RX DV pin */
#define DEV_SM_PIN_ETH0_TXD2                  115U  /*!< ETH0 TXD2 pin */
#define DEV_SM_PIN_ETH0_TXD3                  116U  /*!< ETH0 TXD3 pin */
#define DEV_SM_PIN_ETH0_RXD2                  117U  /*!< ETH0 RXD2 pin */
#define DEV_SM_PIN_ETH0_RXD3                  118U  /*!< ETH0 RXD3 pin */
#define DEV_SM_PIN_ETH0_RX_CLK                119U  /*!< ETH0 RX CLK pin */
#define DEV_SM_PIN_ETH0_RX_ER                 120U  /*!< ETH0 RX ER pin */
#define DEV_SM_PIN_ETH0_TX_ER                 121U  /*!< ETH0 TX ER pin */
#define DEV_SM_PIN_ETH0_CRS                   122U  /*!< ETH0 CRS pin */
#define DEV_SM_PIN_ETH0_COL                   123U  /*!< ETH0 COL pin */
#define DEV_SM_PIN_ETH1_TXD0                  124U  /*!< ETH1 TXD0 pin */
#define DEV_SM_PIN_ETH1_TXD1                  125U  /*!< ETH1 TXD1 pin */
#define DEV_SM_PIN_ETH1_TX_EN                 126U  /*!< ETH1 TX EN pin */
#define DEV_SM_PIN_ETH1_TX_CLK                127U  /*!< ETH1 TX CLK pin */
#define DEV_SM_PIN_ETH1_RXD0                  128U  /*!< ETH1 RXD0 pin */
#define DEV_SM_PIN_ETH1_RXD1                  129U  /*!< ETH1 RXD1 pin */
#define DEV_SM_PIN_ETH1_RX_DV                 130U  /*!< ETH1 RX DV pin */
#define DEV_SM_PIN_ETH1_TXD2                  131U  /*!< ETH1 TXD2 pin */
#define DEV_SM_PIN_ETH1_TXD3                  132U  /*!< ETH1 TXD3 pin */
#define DEV_SM_PIN_ETH1_RXD2                  133U  /*!< ETH1 RXD2 pin */
#define DEV_SM_PIN_ETH1_RXD3                  134U  /*!< ETH1 RXD3 pin */
#define DEV_SM_PIN_ETH1_RX_CLK                135U  /*!< ETH1 RX CLK pin */
#define DEV_SM_PIN_ETH1_RX_ER                 136U  /*!< ETH1 RX ER pin */
#define DEV_SM_PIN_ETH1_TX_ER                 137U  /*!< ETH1 TX ER pin */
#define DEV_SM_PIN_ETH1_CRS                   138U  /*!< ETH1 CRS pin */
#define DEV_SM_PIN_ETH1_COL                   139U  /*!< ETH1 COL pin */
#define DEV_SM_PIN_SD1_CLK                    140U  /*!< SD1 CLK pin */
#define DEV_SM_PIN_SD1_CMD                    141U  /*!< SD1 CMD pin */
#define DEV_SM_PIN_SD1_DATA0                  142U  /*!< SD1 DATA0 pin */
#define DEV_SM_PIN_SD1_DATA1                  143U  /*!< SD1 DATA1 pin */
#define DEV_SM_PIN_SD1_DATA2                  144U  /*!< SD1 DATA2 pin */
#define DEV_SM_PIN_SD1_DATA3                  145U  /*!< SD1 DATA3 pin */
#define DEV_SM_PIN_SD1_DATA4                  146U  /*!< SD1 DATA4 pin */
#define DEV_SM_PIN_SD1_DATA5                  147U  /*!< SD1 DATA5 pin */
#define DEV_SM_PIN_SD1_DATA6                  148U  /*!< SD1 DATA6 pin */
#define DEV_SM_PIN_SD1_DATA7                  149U  /*!< SD1 DATA7 pin */
#define DEV_SM_PIN_SD1_STROBE                 150U  /*!< SD1 STROBE pin */
#define DEV_SM_PIN_SD2_VSELECT                151U  /*!< SD2 VSELECT pin */
#define DEV_SM_PIN_XSPI1_DATA0                152U  /*!< XSPI1 DATA0 pin */
#define DEV_SM_PIN_XSPI1_DATA1                153U  /*!< XSPI1 DATA1 pin */
#define DEV_SM_PIN_XSPI1_DATA2                154U  /*!< XSPI1 DATA2 pin */
#define DEV_SM_PIN_XSPI1_DATA3                155U  /*!< XSPI1 DATA3 pin */
#define DEV_SM_PIN_XSPI1_DATA4                156U  /*!< XSPI1 DATA4 pin */
#define DEV_SM_PIN_XSPI1_DATA5                157U  /*!< XSPI1 DATA5 pin */
#define DEV_SM_PIN_XSPI1_DATA6                158U  /*!< XSPI1 DATA6 pin */
#define DEV_SM_PIN_XSPI1_DATA7                159U  /*!< XSPI1 DATA7 pin */
#define DEV_SM_PIN_XSPI1_DQS                  160U  /*!< XSPI1 DQS pin */
#define DEV_SM_PIN_XSPI1_SCLK                 161U  /*!< XSPI1 SCLK pin */
#define DEV_SM_PIN_XSPI1_SS0_B                162U  /*!< XSPI1 SS0 B pin */
#define DEV_SM_PIN_XSPI1_SS1_B                163U  /*!< XSPI1 SS1 B pin */
#define DEV_SM_PIN_SD2_CD_B                   164U  /*!< SD2 CD B pin */
#define DEV_SM_PIN_SD2_CLK                    165U  /*!< SD2 CLK pin */
#define DEV_SM_PIN_SD2_CMD                    166U  /*!< SD2 CMD pin */
#define DEV_SM_PIN_SD2_DATA0                  167U  /*!< SD2 DATA0 pin */
#define DEV_SM_PIN_SD2_DATA1                  168U  /*!< SD2 DATA1 pin */
#define DEV_SM_PIN_SD2_DATA2                  169U  /*!< SD2 DATA2 pin */
#define DEV_SM_PIN_SD2_DATA3                  170U  /*!< SD2 DATA3 pin */
#define DEV_SM_PIN_SD2_RESET_B                171U  /*!< SD2 RESET B pin */
#define DEV_SM_PIN_SD2_GPIO0                  172U  /*!< SD2 GPIO0 pin */
#define DEV_SM_PIN_SD2_GPIO1                  173U  /*!< SD2 GPIO1 pin */
#define DEV_SM_PIN_SD2_GPIO2                  174U  /*!< SD2 GPIO2 pin */
#define DEV_SM_PIN_SD2_GPIO3                  175U  /*!< SD2 GPIO3 pin */
#define DEV_SM_PIN_I2C1_SCL                   176U  /*!< I2C1 SCL pin */
#define DEV_SM_PIN_I2C1_SDA                   177U  /*!< I2C1 SDA pin */
#define DEV_SM_PIN_I2C2_SCL                   178U  /*!< I2C2 SCL pin */
#define DEV_SM_PIN_I2C2_SDA                   179U  /*!< I2C2 SDA pin */
#define DEV_SM_PIN_UART1_RXD                  180U  /*!< UART1 RXD pin */
#define DEV_SM_PIN_UART1_TXD                  181U  /*!< UART1 TXD pin */
#define DEV_SM_PIN_UART2_RXD                  182U  /*!< UART2 RXD pin */
#define DEV_SM_PIN_UART2_TXD                  183U  /*!< UART2 TXD pin */
#define DEV_SM_PIN_PDM_CLK                    184U  /*!< PDM CLK pin */
#define DEV_SM_PIN_PDM_BIT_STREAM0            185U  /*!< PDM BIT STREAM0 pin */
#define DEV_SM_PIN_PDM_BIT_STREAM1            186U  /*!< PDM BIT STREAM1 pin */
#define DEV_SM_PIN_SAI1_TXFS                  187U  /*!< SAI1 TXFS pin */
#define DEV_SM_PIN_SAI1_TXC                   188U  /*!< SAI1 TXC pin */
#define DEV_SM_PIN_SAI1_TXD0                  189U  /*!< SAI1 TXD0 pin */
#define DEV_SM_PIN_SAI1_RXD0                  190U  /*!< SAI1 RXD0 pin */
#define DEV_SM_PIN_WDOG_ANY                   191U  /*!< WDOG ANY pin */
#define DEV_SM_PIN_FCCU_ERR0                  192U  /*!< FCCU ERR0 pin */
/** @} */

/*!
 * @name Device pin daisy indexes
 */
/** @{ */
#define DEV_SM_DAISY_CAN1_RX              0U    /*!< CAN1 RX daisy */
#define DEV_SM_DAISY_GPT1_CLKIN           1U    /*!< GPT1 CLKIN daisy */
#define DEV_SM_DAISY_PDM_BITSTREAM_0      2U    /*!< PDM BITSTREAM 0 daisy */
#define DEV_SM_DAISY_PDM_BITSTREAM_1      3U    /*!< PDM BITSTREAM 1 daisy */
#define DEV_SM_DAISY_PDM_BITSTREAM_2      4U    /*!< PDM BITSTREAM 2 daisy */
#define DEV_SM_DAISY_PDM_BITSTREAM_3      5U    /*!< PDM BITSTREAM 3 daisy */
#define DEV_SM_DAISY_SAI1_MCLK            6U    /*!< SAI1 MCLK daisy */
#define DEV_SM_DAISY_EXT1_CLK             7U    /*!< EXT1 CLK daisy */
#define DEV_SM_DAISY_ECAT_MDIO            8U    /*!< ECAT MDIO daisy */
#define DEV_SM_DAISY_ECAT_PROM            9U    /*!< ECAT PROM daisy */
#define DEV_SM_DAISY_ETH4_RX_CLK          10U   /*!< ETH4 RX CLK daisy */
#define DEV_SM_DAISY_ETH4_RX_CTL          11U   /*!< ETH4 RX CTL daisy */
#define DEV_SM_DAISY_ETH4_RXD_0           12U   /*!< ETH4 RXD 0 daisy */
#define DEV_SM_DAISY_ETH4_RXD_1           13U   /*!< ETH4 RXD 1 daisy */
#define DEV_SM_DAISY_ETH4_RXD_2           14U   /*!< ETH4 RXD 2 daisy */
#define DEV_SM_DAISY_ETH4_RXD_3           15U   /*!< ETH4 RXD 3 daisy */
#define DEV_SM_DAISY_ETH4_TX_CLK          16U   /*!< ETH4 TX CLK daisy */
#define DEV_SM_DAISY_NETC_1588MUX_0       17U   /*!< NETC 1588MUX 0 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_1       18U   /*!< NETC 1588MUX 1 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_2       19U   /*!< NETC 1588MUX 2 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_3       20U   /*!< NETC 1588MUX 3 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_4       21U   /*!< NETC 1588MUX 4 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_5       22U   /*!< NETC 1588MUX 5 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_6       23U   /*!< NETC 1588MUX 6 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_7       24U   /*!< NETC 1588MUX 7 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_8       25U   /*!< NETC 1588MUX 8 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_9       26U   /*!< NETC 1588MUX 9 daisy */
#define DEV_SM_DAISY_NETC_1588MUX_10      27U   /*!< NETC 1588MUX 10 daisy */
#define DEV_SM_DAISY_NETC_CMPLX_EMDIO     28U   /*!< NETC CMPLX EMDIO daisy */
#define DEV_SM_DAISY_CAN2_RX              29U   /*!< CAN2 RX daisy */
#define DEV_SM_DAISY_CAN3_RX              30U   /*!< CAN3 RX daisy */
#define DEV_SM_DAISY_CAN4_RX              31U   /*!< CAN4 RX daisy */
#define DEV_SM_DAISY_CAN5_RX              32U   /*!< CAN5 RX daisy */
#define DEV_SM_DAISY_ENCODER2_CLK         33U   /*!< ENCODER2 CLK daisy */
#define DEV_SM_DAISY_ENCODER2_IN          34U   /*!< ENCODER2 IN daisy */
#define DEV_SM_DAISY_FLEXIO2_11           35U   /*!< FLEXIO2 11 daisy */
#define DEV_SM_DAISY_FLEXPWM1_PWMX_0      36U   /*!< FLEXPWM1 PWMX 0 daisy */
#define DEV_SM_DAISY_FLEXPWM1_PWMX_1      37U   /*!< FLEXPWM1 PWMX 1 daisy */
#define DEV_SM_DAISY_FLEXPWM2_PWMX_0      38U   /*!< FLEXPWM2 PWMX 0 daisy */
#define DEV_SM_DAISY_FLEXPWM2_PWMX_1      39U   /*!< FLEXPWM2 PWMX 1 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMA_0      40U   /*!< FLEXPWM3 PWMA 0 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMA_1      41U   /*!< FLEXPWM3 PWMA 1 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMA_2      42U   /*!< FLEXPWM3 PWMA 2 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMA_3      43U   /*!< FLEXPWM3 PWMA 3 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMB_0      44U   /*!< FLEXPWM3 PWMB 0 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMB_1      45U   /*!< FLEXPWM3 PWMB 1 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMB_2      46U   /*!< FLEXPWM3 PWMB 2 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMB_3      47U   /*!< FLEXPWM3 PWMB 3 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMX_0      48U   /*!< FLEXPWM3 PWMX 0 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMX_1      49U   /*!< FLEXPWM3 PWMX 1 daisy */
#define DEV_SM_DAISY_FLEXPWM3_PWMX_2      50U   /*!< FLEXPWM3 PWMX 2 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMA_0      51U   /*!< FLEXPWM4 PWMA 0 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMA_1      52U   /*!< FLEXPWM4 PWMA 1 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMA_2      53U   /*!< FLEXPWM4 PWMA 2 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMA_3      54U   /*!< FLEXPWM4 PWMA 3 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMB_0      55U   /*!< FLEXPWM4 PWMB 0 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMB_1      56U   /*!< FLEXPWM4 PWMB 1 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMB_2      57U   /*!< FLEXPWM4 PWMB 2 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMB_3      58U   /*!< FLEXPWM4 PWMB 3 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMX_0      59U   /*!< FLEXPWM4 PWMX 0 daisy */
#define DEV_SM_DAISY_FLEXPWM4_PWMX_1      60U   /*!< FLEXPWM4 PWMX 1 daisy */
#define DEV_SM_DAISY_GPT_MUX_0            61U   /*!< GPT MUX 0 daisy */
#define DEV_SM_DAISY_GPT_MUX_1            62U   /*!< GPT MUX 1 daisy */
#define DEV_SM_DAISY_GPT_MUX_3            63U   /*!< GPT MUX 3 daisy */
#define DEV_SM_DAISY_GPT_MUX_4            64U   /*!< GPT MUX 4 daisy */
#define DEV_SM_DAISY_GPT_MUX_5            65U   /*!< GPT MUX 5 daisy */
#define DEV_SM_DAISY_GPT_MUX_6            66U   /*!< GPT MUX 6 daisy */
#define DEV_SM_DAISY_GPT_MUX_7            67U   /*!< GPT MUX 7 daisy */
#define DEV_SM_DAISY_GPT_MUX_8            68U   /*!< GPT MUX 8 daisy */
#define DEV_SM_DAISY_GPT_MUX_9            69U   /*!< GPT MUX 9 daisy */
#define DEV_SM_DAISY_I3C2_SCL             70U   /*!< I3C2 SCL daisy */
#define DEV_SM_DAISY_I3C2_SDA             71U   /*!< I3C2 SDA daisy */
#define DEV_SM_DAISY_LPI2C3_HREQ          72U   /*!< LPI2C3 HREQ daisy */
#define DEV_SM_DAISY_LPI2C3_SCL           73U   /*!< LPI2C3 SCL daisy */
#define DEV_SM_DAISY_LPI2C3_SDA           74U   /*!< LPI2C3 SDA daisy */
#define DEV_SM_DAISY_LPI2C4_SCL           75U   /*!< LPI2C4 SCL daisy */
#define DEV_SM_DAISY_LPI2C4_SDA           76U   /*!< LPI2C4 SDA daisy */
#define DEV_SM_DAISY_LPI2C5_SCL           77U   /*!< LPI2C5 SCL daisy */
#define DEV_SM_DAISY_LPI2C5_SDA           78U   /*!< LPI2C5 SDA daisy */
#define DEV_SM_DAISY_LPI2C6_HREQ          79U   /*!< LPI2C6 HREQ daisy */
#define DEV_SM_DAISY_LPI2C6_SCL           80U   /*!< LPI2C6 SCL daisy */
#define DEV_SM_DAISY_LPI2C6_SDA           81U   /*!< LPI2C6 SDA daisy */
#define DEV_SM_DAISY_LPI2C7_SCL           82U   /*!< LPI2C7 SCL daisy */
#define DEV_SM_DAISY_LPI2C7_SDA           83U   /*!< LPI2C7 SDA daisy */
#define DEV_SM_DAISY_LPI2C8_SCL           84U   /*!< LPI2C8 SCL daisy */
#define DEV_SM_DAISY_LPI2C8_SDA           85U   /*!< LPI2C8 SDA daisy */
#define DEV_SM_DAISY_LPIT2_EXT_TRIG_IN_2  86U   /*!< LPIT2 EXT TRIG IN 2 daisy */
#define DEV_SM_DAISY_LPIT3_EXT_TRIG_IN_2  87U   /*!< LPIT3 EXT TRIG IN 2 daisy */
#define DEV_SM_DAISY_LPSPI3_PCS_1         88U   /*!< LPSPI3 PCS 1 daisy */
#define DEV_SM_DAISY_LPSPI4_PCS_2         89U   /*!< LPSPI4 PCS 2 daisy */
#define DEV_SM_DAISY_LPSPI5_PCS_1         90U   /*!< LPSPI5 PCS 1 daisy */
#define DEV_SM_DAISY_LPSPI6_PCS_1         91U   /*!< LPSPI6 PCS 1 daisy */
#define DEV_SM_DAISY_LPSPI7_PCS_1         92U   /*!< LPSPI7 PCS 1 daisy */
#define DEV_SM_DAISY_LPSPI8_PCS_1         93U   /*!< LPSPI8 PCS 1 daisy */
#define DEV_SM_DAISY_LPTMR2_0             94U   /*!< LPTMR2 0 daisy */
#define DEV_SM_DAISY_LPTMR2_1             95U   /*!< LPTMR2 1 daisy */
#define DEV_SM_DAISY_LPTMR2_2             96U   /*!< LPTMR2 2 daisy */
#define DEV_SM_DAISY_LPUART10_CTS         97U   /*!< LPUART10 CTS daisy */
#define DEV_SM_DAISY_LPUART10_RXD         98U   /*!< LPUART10 RXD daisy */
#define DEV_SM_DAISY_LPUART10_TXD         99U   /*!< LPUART10 TXD daisy */
#define DEV_SM_DAISY_LPUART11_RXD         100U  /*!< LPUART11 RXD daisy */
#define DEV_SM_DAISY_LPUART11_TXD         101U  /*!< LPUART11 TXD daisy */
#define DEV_SM_DAISY_LPUART3_CTS          102U  /*!< LPUART3 CTS daisy */
#define DEV_SM_DAISY_LPUART3_RXD          103U  /*!< LPUART3 RXD daisy */
#define DEV_SM_DAISY_LPUART3_TXD          104U  /*!< LPUART3 TXD daisy */
#define DEV_SM_DAISY_LPUART4_CTS          105U  /*!< LPUART4 CTS daisy */
#define DEV_SM_DAISY_LPUART4_RXD          106U  /*!< LPUART4 RXD daisy */
#define DEV_SM_DAISY_LPUART4_TXD          107U  /*!< LPUART4 TXD daisy */
#define DEV_SM_DAISY_LPUART5_CTS          108U  /*!< LPUART5 CTS daisy */
#define DEV_SM_DAISY_LPUART5_RXD          109U  /*!< LPUART5 RXD daisy */
#define DEV_SM_DAISY_LPUART5_TXD          110U  /*!< LPUART5 TXD daisy */
#define DEV_SM_DAISY_LPUART6_CTS          111U  /*!< LPUART6 CTS daisy */
#define DEV_SM_DAISY_LPUART6_RXD          112U  /*!< LPUART6 RXD daisy */
#define DEV_SM_DAISY_LPUART6_TXD          113U  /*!< LPUART6 TXD daisy */
#define DEV_SM_DAISY_LPUART7_RXD          114U  /*!< LPUART7 RXD daisy */
#define DEV_SM_DAISY_LPUART7_TXD          115U  /*!< LPUART7 TXD daisy */
#define DEV_SM_DAISY_LPUART8_RXD          116U  /*!< LPUART8 RXD daisy */
#define DEV_SM_DAISY_LPUART8_TXD          117U  /*!< LPUART8 TXD daisy */
#define DEV_SM_DAISY_LPUART9_RXD          118U  /*!< LPUART9 RXD daisy */
#define DEV_SM_DAISY_LPUART9_TXD          119U  /*!< LPUART9 TXD daisy */
#define DEV_SM_DAISY_SAI2_MCLK            120U  /*!< SAI2 MCLK daisy */
#define DEV_SM_DAISY_SAI2_RXBCLK          121U  /*!< SAI2 RXBCLK daisy */
#define DEV_SM_DAISY_SAI2_RXDATA_0        122U  /*!< SAI2 RXDATA 0 daisy */
#define DEV_SM_DAISY_SAI2_RXSYNC          123U  /*!< SAI2 RXSYNC daisy */
#define DEV_SM_DAISY_SAI2_TXBCLK          124U  /*!< SAI2 TXBCLK daisy */
#define DEV_SM_DAISY_SAI2_TXSYNC          125U  /*!< SAI2 TXSYNC daisy */
#define DEV_SM_DAISY_SAI3_RXBCLK          126U  /*!< SAI3 RXBCLK daisy */
#define DEV_SM_DAISY_SAI3_TXSYNC          127U  /*!< SAI3 TXSYNC daisy */
#define DEV_SM_DAISY_SAI4_MCLK            128U  /*!< SAI4 MCLK daisy */
#define DEV_SM_DAISY_SAI4_RXBCLK          129U  /*!< SAI4 RXBCLK daisy */
#define DEV_SM_DAISY_SAI4_RXDATA_0        130U  /*!< SAI4 RXDATA 0 daisy */
#define DEV_SM_DAISY_SAI4_RXSYNC          131U  /*!< SAI4 RXSYNC daisy */
#define DEV_SM_DAISY_SAI4_TXBCLK          132U  /*!< SAI4 TXBCLK daisy */
#define DEV_SM_DAISY_SAI4_TXSYNC          133U  /*!< SAI4 TXSYNC daisy */
#define DEV_SM_DAISY_SINC4_EMBIT_0        134U  /*!< SINC4 EMBIT 0 daisy */
#define DEV_SM_DAISY_SINC4_EMBIT_1        135U  /*!< SINC4 EMBIT 1 daisy */
#define DEV_SM_DAISY_SINC4_EMBIT_2        136U  /*!< SINC4 EMBIT 2 daisy */
#define DEV_SM_DAISY_SINC4_EMCLK_0        137U  /*!< SINC4 EMCLK 0 daisy */
#define DEV_SM_DAISY_SINC4_EMCLK_1        138U  /*!< SINC4 EMCLK 1 daisy */
#define DEV_SM_DAISY_SINC4_EMCLK_2        139U  /*!< SINC4 EMCLK 2 daisy */
#define DEV_SM_DAISY_TPM3_CH_3            140U  /*!< TPM3 CH 3 daisy */
#define DEV_SM_DAISY_TPM4_CH_3            141U  /*!< TPM4 CH 3 daisy */
#define DEV_SM_DAISY_TPM5_CH_1            142U  /*!< TPM5 CH 1 daisy */
#define DEV_SM_DAISY_TPM5_CH_3            143U  /*!< TPM5 CH 3 daisy */
#define DEV_SM_DAISY_TPM6_CH_1            144U  /*!< TPM6 CH 1 daisy */
#define DEV_SM_DAISY_TPM6_CH_3            145U  /*!< TPM6 CH 3 daisy */
#define DEV_SM_DAISY_TPM6_CLK             146U  /*!< TPM6 CLK daisy */
#define DEV_SM_DAISY_USDHC2_WP_ON         147U  /*!< USDHC2 WP ON daisy */
#define DEV_SM_DAISY_USDHC3_CMD           148U  /*!< USDHC3 CMD daisy */
#define DEV_SM_DAISY_USDHC3_DAT0          149U  /*!< USDHC3 DAT0 daisy */
#define DEV_SM_DAISY_USDHC3_DAT1          150U  /*!< USDHC3 DAT1 daisy */
#define DEV_SM_DAISY_USDHC3_DAT2          151U  /*!< USDHC3 DAT2 daisy */
#define DEV_SM_DAISY_USDHC3_DAT3          152U  /*!< USDHC3 DAT3 daisy */
#define DEV_SM_DAISY_XBAR1_IN_4           153U  /*!< XBAR1 IN 4 daisy */
#define DEV_SM_DAISY_XBAR1_IN_5           154U  /*!< XBAR1 IN 5 daisy */
#define DEV_SM_DAISY_XBAR1_IN_6           155U  /*!< XBAR1 IN 6 daisy */
#define DEV_SM_DAISY_XBAR1_IN_7           156U  /*!< XBAR1 IN 7 daisy */
#define DEV_SM_DAISY_XBAR1_IN_8           157U  /*!< XBAR1 IN 8 daisy */
#define DEV_SM_DAISY_XBAR1_IN_9           158U  /*!< XBAR1 IN 9 daisy */
#define DEV_SM_DAISY_XBAR1_IN_10          159U  /*!< XBAR1 IN 10 daisy */
#define DEV_SM_DAISY_XBAR1_IN_11          160U  /*!< XBAR1 IN 11 daisy */
#define DEV_SM_DAISY_XBAR1_IN_12          161U  /*!< XBAR1 IN 12 daisy */
#define DEV_SM_DAISY_XBAR1_IN_13          162U  /*!< XBAR1 IN 13 daisy */
#define DEV_SM_DAISY_XBAR1_IN_14          163U  /*!< XBAR1 IN 14 daisy */
#define DEV_SM_DAISY_XBAR1_IN_15          164U  /*!< XBAR1 IN 15 daisy */
#define DEV_SM_DAISY_XBAR1_IN_16          165U  /*!< XBAR1 IN 16 daisy */
#define DEV_SM_DAISY_XBAR1_IN_17          166U  /*!< XBAR1 IN 17 daisy */
#define DEV_SM_DAISY_XBAR1_IN_18          167U  /*!< XBAR1 IN 18 daisy */
#define DEV_SM_DAISY_XBAR1_IN_19          168U  /*!< XBAR1 IN 19 daisy */
#define DEV_SM_DAISY_XBAR1_IN_20          169U  /*!< XBAR1 IN 20 daisy */
#define DEV_SM_DAISY_XBAR1_IN_30          170U  /*!< XBAR1 IN 30 daisy */
#define DEV_SM_DAISY_XBAR1_IN_31          171U  /*!< XBAR1 IN 31 daisy */
#define DEV_SM_DAISY_XBAR1_IN_32          172U  /*!< XBAR1 IN 32 daisy */
#define DEV_SM_DAISY_XBAR1_IN_33          173U  /*!< XBAR1 IN 33 daisy */
#define DEV_SM_DAISY_XBAR1_IN_34          174U  /*!< XBAR1 IN 34 daisy */
#define DEV_SM_DAISY_XBAR1_IN_35          175U  /*!< XBAR1 IN 35 daisy */
#define DEV_SM_DAISY_XBAR1_IN_36          176U  /*!< XBAR1 IN 36 daisy */
#define DEV_SM_DAISY_XBAR1_IN_37          177U  /*!< XBAR1 IN 37 daisy */
#define DEV_SM_DAISY_XBAR1_IN_38          178U  /*!< XBAR1 IN 38 daisy */
#define DEV_SM_DAISY_XBAR1_IN_39          179U  /*!< XBAR1 IN 39 daisy */
#define DEV_SM_DAISY_XBAR1_IN_40          180U  /*!< XBAR1 IN 40 daisy */
#define DEV_SM_DAISY_XBAR1_IN_41          181U  /*!< XBAR1 IN 41 daisy */
#define DEV_SM_DAISY_XBAR1_IN_42          182U  /*!< XBAR1 IN 42 daisy */
#define DEV_SM_DAISY_XBAR1_IN_43          183U  /*!< XBAR1 IN 43 daisy */
#define DEV_SM_DAISY_XBAR1_IN_44          184U  /*!< XBAR1 IN 44 daisy */
#define DEV_SM_DAISY_XBAR1_IN_45          185U  /*!< XBAR1 IN 45 daisy */
#define DEV_SM_DAISY_XBAR1_IN_46          186U  /*!< XBAR1 IN 46 daisy */
#define DEV_SM_DAISY_XBAR1_IN_47          187U  /*!< XBAR1 IN 47 daisy */
#define DEV_SM_DAISY_XBAR1_IN_48          188U  /*!< XBAR1 IN 48 daisy */
#define DEV_SM_DAISY_XSPI_CS              189U  /*!< XSPI CS daisy */
#define DEV_SM_DAISY_XSPI_DQS             190U  /*!< XSPI DQS daisy */
#define DEV_SM_DAISY_XSPI_SCK             191U  /*!< XSPI SCK daisy */
#define DEV_SM_DAISY_XSPI_SLV_0           192U  /*!< XSPI SLV 0 daisy */
#define DEV_SM_DAISY_XSPI_SLV_1           193U  /*!< XSPI SLV 1 daisy */
#define DEV_SM_DAISY_XSPI_SLV_2           194U  /*!< XSPI SLV 2 daisy */
#define DEV_SM_DAISY_XSPI_SLV_3           195U  /*!< XSPI SLV 3 daisy */
#define DEV_SM_DAISY_XSPI_SLV_4           196U  /*!< XSPI SLV 4 daisy */
#define DEV_SM_DAISY_XSPI_SLV_5           197U  /*!< XSPI SLV 5 daisy */
#define DEV_SM_DAISY_XSPI_SLV_6           198U  /*!< XSPI SLV 6 daisy */
#define DEV_SM_DAISY_XSPI_SLV_7           199U  /*!< XSPI SLV 7 daisy */
#define DEV_SM_DAISY_JTAG_TCK             200U  /*!< JTAG TCK daisy */
#define DEV_SM_DAISY_JTAG_TDI             201U  /*!< JTAG TDI daisy */
#define DEV_SM_DAISY_JTAG_TMS             202U  /*!< JTAG TMS daisy */
/** @} */

/*!
 * @name Device pin config types
 */
/** @{ */
#define DEV_SM_PIN_TYPE_MUX     0U  /*!< Pin mux */
#define DEV_SM_PIN_TYPE_CONFIG  1U  /*!< Pin config */
#define DEV_SM_PIN_TYPE_DAISY   2U  /*!< Pin daisy */
#define DEV_SM_PIN_TYPE_EXT     3U  /*!< Pin extended */
/** @} */

/* Types */

/* Functions */

/** @} */

/* Include SM device API */

/* coverity[misra_c_2012_rule_20_1_violation] */
#include "dev_sm_pin_api.h"

#endif /* DEV_SM_PIN_H */

