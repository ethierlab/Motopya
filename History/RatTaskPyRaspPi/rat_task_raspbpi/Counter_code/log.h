/****************************************************************************
 **
 ** Copyright (C) 2020 MikroElektronika d.o.o.
 ** Contact: https://www.mikroe.com/contact
 **
 ** This file is part of the mikroSDK package
 **
 ** Commercial License Usage
 **
 ** Licensees holding valid commercial NECTO compilers AI licenses may use this
 ** file in accordance with the commercial license agreement provided with the
 ** Software or, alternatively, in accordance with the terms contained in
 ** a written agreement between you and The mikroElektronika Company.
 ** For licensing terms and conditions see
 ** https://www.mikroe.com/legal/software-license-agreement.
 ** For further information use the contact form at
 ** https://www.mikroe.com/contact.
 **
 **
 ** GNU Lesser General Public License Usage
 **
 ** Alternatively, this file may be used for
 ** non-commercial projects under the terms of the GNU Lesser
 ** General Public License version 3 as published by the Free Software
 ** Foundation: https://www.gnu.org/licenses/lgpl-3.0.html.
 **
 ** The above copyright notice and this permission notice shall be
 ** included in all copies or substantial portions of the Software.
 **
 ** THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 ** OF MERCHANTABILITY, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
 ** TO THE WARRANTIES FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 ** IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
 ** DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
 ** OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
 ** OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 **
 ****************************************************************************/
  
 #ifndef _LOG_H_
 #define _LOG_H_
  
 #ifdef __cplusplus
 extern "C"{
 #endif
  
 #include "../../../generic.h"
 #include "drv_uart.h"
 #include <stdarg.h>
  
 typedef enum
 {
  LOG_LEVEL_DEBUG = 0x00, 
  LOG_LEVEL_INFO = 0x01, 
  LOG_LEVEL_WARNING = 0x02, 
  LOG_LEVEL_ERROR = 0x03, 
  LOG_LEVEL_FATAL = 0x04, 
 } log_level_t;
  
 typedef struct
 {
  uart_t uart; 
  log_level_t log_level; 
 } log_t;
  
 typedef struct
 {
  hal_pin_name_t rx_pin; 
  hal_pin_name_t tx_pin; 
  uint32_t baud; 
  log_level_t level; 
 } log_cfg_t;
  
 #define ABS(x) (((x)>0)?(x):-(x))
  
 #define LOG_MAP_USB_UART(cfg) \
  cfg.rx_pin = USB_UART_RX; \
  cfg.tx_pin = USB_UART_TX; \
  cfg.baud = 9600; \
  cfg.level = LOG_LEVEL_DEBUG;
  
 #define LOG_MAP_MIKROBUS(cfg, mikrobus) \
  cfg.rx_pin = MIKROBUS(mikrobus, MIKROBUS_RX); \
  cfg.tx_pin = MIKROBUS(mikrobus, MIKROBUS_TX); \
  cfg.baud = 9600; \
  cfg.level = LOG_LEVEL_DEBUG;
  
 void log_init ( log_t *log, log_cfg_t *cfg );
  
 void log_printf ( log_t *log, const code char * __generic f,... );
  
 void log_clear ( log_t *log );
  
 int8_t log_read ( log_t *log, uint8_t *rx_data_buf, uint8_t max_len );
  
 void log_info ( log_t *log, const code char * __generic f,... );
  
 void log_error ( log_t *log, const code char * __generic f,... );
  
 void log_fatal ( log_t *log, const code char * __generic f,... );
  
 void log_debug ( log_t *log, const code char * __generic f,... );
  
 void log_warning ( log_t *log, const code char * __generic f,... );
  
 void log_log ( log_t *log, char * prefix, const code char * __generic f, ... );
  // loggroup // apigroup
  
 #ifdef __cplusplus
 }
 #endif
 #endif // _LOG_H_
 // ------------------------------------------------------------------------- END