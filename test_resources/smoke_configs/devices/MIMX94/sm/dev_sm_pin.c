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

/*==========================================================================*/
/* File containing the implementation of the device pins.                   */
/*==========================================================================*/

/* Includes */

#include "sm.h"
#include "dev_sm.h"
#include "fsl_iomuxc.h"

/* Local defines */

#define GPIO_CTRL(CTRL, SEL)  (0x80U | ((SEL) << 4U) | (CTRL))
#define MAP_CTRL(X)           ((X) & 0xFU)
#define MAP_SEL(X)            (((X) & 0x70U) >> 4U)
#define GPIO_SET(SEL, X)      ((X) << ((SEL) * 4U))
#define GPIO_GET(SEL, X)      (((X) >> ((SEL) * 4U)) & 0xFU)

/* Macro to check the iomux offset overflow */
#define IOMUX_OFFSET_OVERFLOW_CHECK    0xF000U

/* Local types */

/* Local variables */

static uint8_t gpioCtrlMap[DEV_SM_NUM_PIN] =
{
    [DEV_SM_PIN_GPIO_IO17] = GPIO_CTRL(0U, 0U),
    [DEV_SM_PIN_GPIO_IO18] = GPIO_CTRL(0U, 1U),
    [DEV_SM_PIN_GPIO_IO19] = GPIO_CTRL(0U, 2U),
    [DEV_SM_PIN_GPIO_IO37] = GPIO_CTRL(0U, 3U),
    [DEV_SM_PIN_GPIO_IO55] = GPIO_CTRL(0U, 4U),
    [DEV_SM_PIN_GPIO_IO57] = GPIO_CTRL(0U, 5U),
    [DEV_SM_PIN_CCM_CLKO3] = GPIO_CTRL(0U, 6U),
    [DEV_SM_PIN_ETH4_TXD2] = GPIO_CTRL(0U, 7U),
    [DEV_SM_PIN_XSPI1_SS1_B] = GPIO_CTRL(1U, 0U),
    [DEV_SM_PIN_ETH4_MDIO_GPIO2] = GPIO_CTRL(1U, 1U),
    [DEV_SM_PIN_ETH4_RX_CTL] = GPIO_CTRL(1U, 2U),
};

/*--------------------------------------------------------------------------*/
/* Return pin name                                                          */
/*--------------------------------------------------------------------------*/
int32_t DEV_SM_PinNameGet(uint32_t identifier, string *pinNameAddr,
    int32_t *len)
{
    int32_t status = SM_ERR_SUCCESS;
    static int32_t s_maxLen = 0;

    static string const s_name[DEV_SM_NUM_PIN] =
    {
        "daptdi",
        "daptmsswdio",
        "daptclkswclk",
        "daptdotraceswo",
        "gpioio00",
        "gpioio01",
        "gpioio02",
        "gpioio03",
        "gpioio04",
        "gpioio05",
        "gpioio06",
        "gpioio07",
        "gpioio08",
        "gpioio09",
        "gpioio10",
        "gpioio11",
        "gpioio12",
        "gpioio13",
        "gpioio14",
        "gpioio15",
        "gpioio16",
        "gpioio17",
        "gpioio18",
        "gpioio19",
        "gpioio20",
        "gpioio21",
        "gpioio22",
        "gpioio23",
        "gpioio24",
        "gpioio25",
        "gpioio26",
        "gpioio27",
        "gpioio28",
        "gpioio29",
        "gpioio30",
        "gpioio31",
        "gpioio32",
        "gpioio33",
        "gpioio34",
        "gpioio35",
        "gpioio36",
        "gpioio37",
        "gpioio38",
        "gpioio39",
        "gpioio40",
        "gpioio41",
        "gpioio42",
        "gpioio43",
        "gpioio44",
        "gpioio45",
        "gpioio46",
        "gpioio47",
        "gpioio48",
        "gpioio49",
        "gpioio50",
        "gpioio51",
        "gpioio52",
        "gpioio53",
        "gpioio54",
        "gpioio55",
        "gpioio56",
        "gpioio57",
        "ccmclko1",
        "ccmclko2",
        "ccmclko3",
        "ccmclko4",
        "eth2mdcgpio1",
        "eth2mdiogpio2",
        "eth2txd3",
        "eth2txd2",
        "eth2txd1",
        "eth2txd0",
        "eth2txctl",
        "eth2txclk",
        "eth2rxctl",
        "eth2rxclk",
        "eth2rxd0",
        "eth2rxd1",
        "eth2rxd2",
        "eth2rxd3",
        "eth3mdcgpio1",
        "eth3mdiogpio2",
        "eth3txd3",
        "eth3txd2",
        "eth3txd1",
        "eth3txd0",
        "eth3txctl",
        "eth3txclk",
        "eth3rxctl",
        "eth3rxclk",
        "eth3rxd0",
        "eth3rxd1",
        "eth3rxd2",
        "eth3rxd3",
        "eth4mdcgpio1",
        "eth4mdiogpio2",
        "eth4txclk",
        "eth4txctl",
        "eth4txd0",
        "eth4txd1",
        "eth4txd2",
        "eth4txd3",
        "eth4rxd0",
        "eth4rxd1",
        "eth4rxd2",
        "eth4rxd3",
        "eth4rxctl",
        "eth4rxclk",
        "eth0txd0",
        "eth0txd1",
        "eth0txen",
        "eth0txclk",
        "eth0rxd0",
        "eth0rxd1",
        "eth0rxdv",
        "eth0txd2",
        "eth0txd3",
        "eth0rxd2",
        "eth0rxd3",
        "eth0rxclk",
        "eth0rxer",
        "eth0txer",
        "eth0crs",
        "eth0col",
        "eth1txd0",
        "eth1txd1",
        "eth1txen",
        "eth1txclk",
        "eth1rxd0",
        "eth1rxd1",
        "eth1rxdv",
        "eth1txd2",
        "eth1txd3",
        "eth1rxd2",
        "eth1rxd3",
        "eth1rxclk",
        "eth1rxer",
        "eth1txer",
        "eth1crs",
        "eth1col",
        "sd1clk",
        "sd1cmd",
        "sd1data0",
        "sd1data1",
        "sd1data2",
        "sd1data3",
        "sd1data4",
        "sd1data5",
        "sd1data6",
        "sd1data7",
        "sd1strobe",
        "sd2vselect",
        "xspi1data0",
        "xspi1data1",
        "xspi1data2",
        "xspi1data3",
        "xspi1data4",
        "xspi1data5",
        "xspi1data6",
        "xspi1data7",
        "xspi1dqs",
        "xspi1sclk",
        "xspi1ss0b",
        "xspi1ss1b",
        "sd2cdb",
        "sd2clk",
        "sd2cmd",
        "sd2data0",
        "sd2data1",
        "sd2data2",
        "sd2data3",
        "sd2resetb",
        "sd2gpio0",
        "sd2gpio1",
        "sd2gpio2",
        "sd2gpio3",
        "i2c1scl",
        "i2c1sda",
        "i2c2scl",
        "i2c2sda",
        "uart1rxd",
        "uart1txd",
        "uart2rxd",
        "uart2txd",
        "pdmclk",
        "pdmbitstream0",
        "pdmbitstream1",
        "sai1txfs",
        "sai1txc",
        "sai1txd0",
        "sai1rxd0",
        "wdogany",
        "fccuerr0"
    };

    /* Get max string width */
    DEV_SM_MaxStringGet(len, &s_maxLen, s_name, DEV_SM_NUM_PIN);

    /* Check domain */
    if (identifier >= DEV_SM_NUM_PIN)
    {
        status = SM_ERR_NOT_FOUND;
    }
    else
    {
        /* Return pointer to name */
        *pinNameAddr = s_name[identifier];
    }

    /* Return status */
    return status;
}

/*--------------------------------------------------------------------------*/
/* Set pin config                                                           */
/*--------------------------------------------------------------------------*/
void DEV_SM_PinConfigSet(uint32_t type, uint32_t identifier, uint32_t value)
{
    /* Check for invalid variable identifier's value */
    if ((identifier & IOMUX_OFFSET_OVERFLOW_CHECK) == 0U)
    {
        /* Handle Mux */
        if (type == DEV_SM_PIN_TYPE_MUX)
        {
            uint32_t muxRegister = IOMUXC_BASE + (identifier * 4U);
            uint32_t inputOnfield = 0U;

            /* Extract SION */
            if ((value & ((uint32_t) IOMUXC_PAD_SION_MASK)) != 0U)
            {
                inputOnfield = 1U;
            }

            IOMUXC_SetPinMux(muxRegister, value, 0U, 0U, 0U, inputOnfield);
        }

        /* Handle Config */
        else if (type == DEV_SM_PIN_TYPE_CONFIG)
        {
            uint32_t configRegister = IOMUXC_BASE + (DEV_SM_NUM_PIN * 4U)
                + (identifier * 4U);

            IOMUXC_SetPinConfig(0U, 0U, 0U, 0U, configRegister, value);
        }

        /* Handle Daisy */
        else if (type == DEV_SM_PIN_TYPE_DAISY)
        {
            uint32_t daisyRegister = IOMUXC_BASE + (DEV_SM_NUM_PIN * 8U)
                + (identifier * 4U);

            IOMUXC_SetPinMux(0U, 0U, daisyRegister, value, 0U, 0U);
        }

        /* Handle Extended */
        else if (type == DEV_SM_PIN_TYPE_EXT)
        {
            uint32_t gpioCtrl = gpioCtrlMap[identifier];

            /* Check if mux extended */
            if (gpioCtrl != 0U)
            {
                uint32_t ctrl = MAP_CTRL(gpioCtrl);
                uint32_t sel =  MAP_SEL(gpioCtrl);
                volatile uint32_t *addr;
                uint32_t tmp;

                /* Determine address */
                switch (ctrl)
                {
                    case 0U:
                        addr = &BLK_CTRL_WAKEUPMIX->IOMUX_GPIO_CTRL_0;
                        break;
                    case 1U:
                        addr = &BLK_CTRL_WAKEUPMIX->IOMUX_GPIO_CTRL_1;
                        break;
                    default:
                        addr = &BLK_CTRL_WAKEUPMIX->IOMUX_GPIO_CTRL_5;
                        break;
                }

                /* Read register */
                tmp = *addr;

                /* Clear mux override and sel */
                tmp &= ~(GPIO_SET(sel, 0xFUL));

                /* Set mux override and sel */
                tmp |= GPIO_SET(sel, value & 0xFUL);

                /* Write register */
                *addr = tmp;
            }
        }

        /* Else */
        else
        {
            ; /* Intentional empty else */
        }
    }
    else
    {
        ; /* Intentional empty else */
    }
}

/*--------------------------------------------------------------------------*/
/* Get pin config                                                           */
/*--------------------------------------------------------------------------*/
void DEV_SM_PinConfigGet(uint32_t type, uint32_t identifier, uint32_t *value)
{
    /* Check for invalid variable identifier's value */
    if ((identifier & IOMUX_OFFSET_OVERFLOW_CHECK) == 0U)
    {
        *value = 0U;

        /* Handle Mux */
        if (type == DEV_SM_PIN_TYPE_MUX)
        {
            uint32_t muxRegister = IOMUXC_BASE + (identifier * 4U);

            /* Get IOMUXC value */
            *value = *((volatile uint32_t*) muxRegister);
        }

        /* Handle Config */
        else if (type == DEV_SM_PIN_TYPE_CONFIG)
        {
            uint32_t configRegister = IOMUXC_BASE + (DEV_SM_NUM_PIN * 4U)
                + (identifier * 4U);

            *value =  *((volatile uint32_t*) configRegister);
        }

        /* Handle Daisy */
        else if (type == DEV_SM_PIN_TYPE_DAISY)
        {
            uint32_t daisyRegister = IOMUXC_BASE + (DEV_SM_NUM_PIN * 8U)
                + (identifier * 4U);

            *value = *((volatile uint32_t*) daisyRegister);
        }

        /* Handle Extended */
        else if (type == DEV_SM_PIN_TYPE_EXT)
        {
            uint32_t gpioCtrl = gpioCtrlMap[identifier];

            /* Check if mux extended */
            if (gpioCtrl != 0U)
            {
                uint32_t ctrl = MAP_CTRL(gpioCtrl);
                uint32_t sel =  MAP_SEL(gpioCtrl);
                const volatile uint32_t *addr;

                /* Determine address */
                switch (ctrl)
                {
                    case 0U:
                        addr = &BLK_CTRL_WAKEUPMIX->IOMUX_GPIO_CTRL_0;
                        break;
                    case 1U:
                        addr = &BLK_CTRL_WAKEUPMIX->IOMUX_GPIO_CTRL_1;
                        break;
                    default:
                        addr = &BLK_CTRL_WAKEUPMIX->IOMUX_GPIO_CTRL_5;
                        break;
                }

                /* Read register */
                *value = GPIO_GET(sel, *addr);
            }
            else
            {
                *value = 0U;
            }
        }

        /* Else */
        else
        {
            ; /* Intentional empty else */
        }
    }
    else
    {
        ; /* Intentional empty else */
    }
}

