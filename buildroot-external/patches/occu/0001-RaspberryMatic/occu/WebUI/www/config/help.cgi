#!/bin/tclsh
source cgi.tcl
source common.tcl
load tclrega.so

set PRODUCT_NAME "RaspberryMatic"
set PRODUCT_ID "CCU"
# set HOMEMATIC_URL "http://www.homematic.com"
set HOMEMATIC_URL "http://www.eq-3.de"
set HOMEMATIC_IP_URL "https://www.homematic-ip.com"


set HM_INFO_URL "$HOMEMATIC_URL/produkte/homematic.html"
set IP_INFO_URL "$HOMEMATIC_IP_URL/start.html"

set HM_HELP_URL "$HOMEMATIC_URL/service.html"
set IP_HELP_URL "$HOMEMATIC_IP_URL/service.html"

set LANGUAGE "de"
set CUR_YEAR [clock format [clock seconds] -format %Y]

proc loadVarsFromShellFile {filename arrayName} {
    upvar 1 $arrayName array
    set f [open $filename]
    while {[gets $f line] >= 0} {
        if {[regexp {^\s*(\w+)=([""'']?)(.*)\2\s*$} $line -> key quote value]} {
            if {$value == ""} {
              set array($key) "n/a"
            } else {
              set array($key) $value
            }
        }
    }
    close $f
}

proc putsVar {name value} {
    puts "<div style='display: table-row;'><div style='display:table-cell; width: 50%; text-align: right;'>$name:</div><div style='display:table-cell; width: 50%; text-align: left;'>$value</div></div>"
}

proc action_put_page {} {
  global PRODUCT_NAME PRODUCT_ID HOMEMATIC_URL HOMEMATIC_IP_URL HM_HELP_URL IP_HELP_URL HM_INFO_URL IP_INFO_URL LANGUAGE CUR_YEAR env

  # get all variables from /var/hm_mode into $hm array
  loadVarsFromShellFile /var/hm_mode hm

  # get all variables from /VERSION into ver array
  loadVarsFromShellFile /VERSION ver

  set SERIAL ""
  catch {set SERIAL $hm(HM_HMIP_SERIAL)}
  if {$SERIAL == ""} {
    if {[file exist /var/board_sgtin]} {
      set SERIAL [exec cat /var/board_sgtin]
    } elseif {[file exist /var/board_serial]} {
      set SERIAL [exec cat /var/board_serial]
    } elseif {[file exist /sys/module/plat_eq3ccu2/parameters/board_serial]} {
      set SERIAL [exec cat /sys/module/plat_eq3ccu2/parameters/board_serial]
    } else {
      set SERIAL "n/a"
    }
  }

  set HWMODEL "n/a"
  if {[file exist /proc/device-tree/model]} {
    set HWMODEL [exec cat /proc/device-tree/model]
  } elseif {[file exist /sys/devices/virtual/dmi/id/sys_vendor]} {
    set VENDOR [exec cat /sys/devices/virtual/dmi/id/sys_vendor]
    set PNAME ""
    if {[file exist /sys/devices/virtual/dmi/id/product_name]} {
      set PNAME [exec cat /sys/devices/virtual/dmi/id/product_name]
    }
    set HWMODEL "$VENDOR $PNAME"
  }

  set CPUMODEL [exec lscpu | grep "Model name:" | cut -d: -f2 | xargs echo -n]
  set NUMCPU [exec nproc]
  set LOADAVG [exec awk {{ printf $1 " " $2 " " $3 }} /proc/loadavg]
  set MEM [exec free -h | grep Mem: | awk {{ print $2 }}]
  set MEMUSE [exec egrep "Mem(Total|Available)" /proc/meminfo | tr -d "\n" | awk {{ printf("%.1f %", 100-$4/$2*100) }}]
  set SWAPUSE [exec egrep "Swap(Total|Free)" /proc/meminfo | tr -d "\n" | awk {{ printf("%.1f %", 100-$4/$2*100) }}]
  set UPTIME [exec awk {{s=int($1);d=int(s/86400);h=int(s % 86400/3600);m=int(s % 3600 / 60); printf "%d d, %d h %d min", d, h, m}} /proc/uptime]
  set NTPOFFSET [exec /usr/bin/chronyc -n tracking | grep "Last offset" | awk {{ printf("%.3f ms", $4*1000) }}]
  catch {set OSTYPE [string trim [read_var /etc/os-release PRETTY_NAME] '"']}
  set OSKERNEL [exec uname -s -r -m]
  set TCLVER [info patchlevel]
  set TEMP "n/a"
  if {[file exist /sys/class/thermal/thermal_zone0/temp]} {
    set TEMP [exec awk {{ printf("%.1f &deg;C", $1/1000) }} /sys/class/thermal/thermal_zone0/temp]
  }
  set STATUS ""
  if {[file exist /var/status/hasIP]} {
    set STATUS "IP(1) $STATUS"
  } else {
    set STATUS "IP(0) $STATUS"
  }
  if {[file exist /var/status/hasInternet]} {
    set STATUS "Internet(1) $STATUS"
  } else {
    set STATUS "Internet(0) $STATUS"
  }
  if {[file exist /var/status/hasLink]} {
    set STATUS "Link(1) $STATUS"
  } else {
    set STATUS "Link(0) $STATUS"
  }
  if {[file exist /var/status/hasNTP]} {
    set STATUS "NTP(1) $STATUS"
  } else {
    set STATUS "NTP(0) $STATUS"
  }
  if {[file exist /var/status/hasSD]} {
    set STATUS "SD(1) $STATUS"
  } else {
    set STATUS "SD(0) $STATUS"
  }
  set ROOTFSFREE [exec monit status rootfs | grep "space free total" | awk {{ print substr($0,index($0,$4)) }}]
  set USERFSFREE [exec monit status userfs | grep "space free total" | awk {{ print substr($0,index($0,$4)) }}]
  set STORAGEDEV [exec mountpoint -n / | awk {{ print $1 }} | xargs lsblk -l -n -o PKNAME -p]
  set STORAGE "n/a"
  if {$STORAGEDEV != "" } {
    set STORAGE [exec lsblk -l -n -o SIZE,MODEL,KNAME -d -p $STORAGEDEV]
  }

  set sid ""
  catch {import sid}
  set from ""
  catch {import from}

  #<%
  #  system.SetSessionVar("sessionTAB", "help");
  #%>

  if { "$from" == "internal" } {
    puts {
      <script type="text/javascript">
        setPath(translateKey('dialogHelpPath'));
      </script>
    }
  }

  puts "<table id='overviewHelpPage' class='CLASS21300' style='display:none'>"
    puts "<colgroup>"
    puts "<col style='width:50%;'/>"
    puts "<col style='width:50%;'/>"
    puts "</colgroup>"
    puts "<tr>"

      puts "<td id='tdInfo' class='CLASS21305a' >"
        puts "<img src='/ise/img/rm-logo_small.png'/><br/>"
        puts "\${dialogHelpInfoLblVersion} $ver(VERSION) ($ver(PLATFORM))<br/>"
        puts "<br/>\${dialogHelpInfoLblCopyright} &copy; 2016 - $CUR_YEAR<br/>"
        puts "RaspberryMatic Contributors (<a target='_blank' href='https://github.com/jens-maus/RaspberryMatic/graphs/contributors'>see here</a>)<br/>"
        puts "Licensed under Apache 2.0 OpenSource license<br/>"
        puts "<a target='_blank' href=\"https://github.com/jens-maus/RaspberryMatic/\">https://github.com/jens-maus/RaspberryMatic/</a><br/>"
        puts "<a target='_blank' href=\"https://raspberrymatic.de/\">https://raspberrymatic.de/</a><br/>"
        puts "<br/>Based on <a target='_blank' href=\"https://github.com/eq-3/occu\">OCCU-SDK</a>:<br/>"
        puts "\${dialogHelpInfoLblCopyright} &copy; 2007 - $CUR_YEAR<br/>"
        puts "eQ-3 AG, 26789 Leer, Germany<br/>"
        puts "<a target='_blank' href=\"$HM_INFO_URL\">\${homepage} \${LabelHomeMatic}</a><br/>"
        puts "<a target='_blank' href=\"$IP_INFO_URL\">\${homepage} \${dialogHelpLinkOnlineHelpB}</a><br/>"
        puts "<br/>Menu icons made by <a target='_blank' href=\"https://icons8.com/license/\">icons8.com</a><br/>"
        puts "<br/>\${dialogSettingsCMHintSoftwareUpdateRaspMatic}</a><br/><br/>"
        puts "<h1 class='helpTitle'><u>\${menuHelpPage}</u></h1>"
        puts "<a target='_blank' href='https://github.com/jens-maus/RaspberryMatic/wiki'>RaspberryMatic Documentation</a><br/>"
        puts "<a target='_blank' href=\'$HM_HELP_URL\'>\${dialogHelpLinkOnlineHelpA}</a><br/>"
        puts "<a target='_blank' href=\'$IP_HELP_URL\'>\${dialogHelpLinkOnlineHelpB}</a><br/>"
        puts "<a target='_blank' href='/licenseinfo.htm'>\${lblLicenseInformation}</a><br/>"
      puts "</td>"

      puts "<td id='tdOnline' class='CLASS21301a'  style='text-align:center;'>"
        puts "<h1 class='helpTitle'><u>CCU Hardware Info</u></h1>"
        puts "<div style='display: table; width: 100%;'>"
          putsVar "Serial Number" $SERIAL
          putsVar "Hardware Model" "$HWMODEL ($hm(HM_HOST))"
          putsVar "CPU / Memory" "$CPUMODEL ($NUMCPU), $MEM"
          putsVar "Storage" "$STORAGE"
          putsVar "Real-Time-Clock" $hm(HM_RTC)
        puts "</div>"
        puts "<h1 class='helpTitle'><u>CCU Software Info</u></h1>"
        puts "<div style='display: table; width: 100%;'>"
          putsVar "Product" "$ver(PRODUCT) ($ver(VERSION))"
          putsVar "ReGaHss" [rega dom.BuildLabel()]
          putsVar "TCL" "$TCLVER"
          putsVar "Status" $STATUS
        puts "</div>"
        puts "<h1 class='helpTitle'><u>Operating System Info</u></h1>"
        puts "<div style='display: table; width: 100%;'>"
          putsVar "OS Type/Kernel" "$OSTYPE ($OSKERNEL)"
          putsVar "Uptime" $UPTIME
          putsVar "Load Average" $LOADAVG
          putsVar "System Temperature" $TEMP
          putsVar "Memory / Swap Utilization" "$MEMUSE / $SWAPUSE"
          putsVar "NTP Offset" $NTPOFFSET
          putsVar "rootfs / userfs Free Space" "$ROOTFSFREE / $USERFSFREE"
        puts "</div>"
        puts "<h1 class='helpTitle'><u>homematicIP-RF (HmIP) Info</u></h1>"
        puts "<div style='display: table; width: 100%;'>"
          putsVar "RF-Module/Firmware" "$hm(HM_HMIP_DEV) ($hm(HM_HMIP_VERSION))"
          putsVar "Device-Node" "$hm(HM_HMIP_DEVNODE) ($hm(HM_HMIP_DEVTYPE))"
          putsVar "Address" "$hm(HM_HMIP_ADDRESS) ($hm(HM_HMIP_ADDRESS_ACTIVE))"
          putsVar "SGTIN" $hm(HM_HMIP_SGTIN)
          putsVar "Serial" $hm(HM_HMIP_SERIAL)
        puts "</div>"
        puts "<h1 class='helpTitle'><u>HomeMatic-RF (HmRF) Info</u></h1>"
        puts "<div style='display: table; width: 100%;'>"
          putsVar "RF-Module/Firmware" "$hm(HM_HMRF_DEV) ($hm(HM_HMRF_VERSION))"
          putsVar "Device-Node" "$hm(HM_HMRF_DEVNODE) ($hm(HM_HMRF_DEVTYPE))"
          putsVar "Address" "$hm(HM_HMRF_ADDRESS) ($hm(HM_HMRF_ADDRESS_ACTIVE))"
          putsVar "Serial" $hm(HM_HMRF_SERIAL)
        puts "</div>"
      puts "</td>"

  puts "</table>"


  cgi_javascript {
    if { "$from" == "internal" } {
      set href ""
      puts "setFooter('');"
    } else {
      if { "$from" != "login" } {
        set href "/pages/index.htm?NoAutoLogin=true"
      } else {
        set href "/"
        set queryparams ""
        set queryparams [cgi_unquote_input $env(QUERY_STRING)]
        set querysid ""
        if { [regexp "sid=(@\[A-Za-z0-9\]*@)" $queryparams dummy querysid] } then {
          set href "login.htm?sid=$querysid"
        }
      }

      puts "var s = \"\";"
      puts "s += \"<table cellspacing='8' >\";"
      puts "s += \"<tbody>\";"
      puts "s += \"<tr>\";"
      puts "s += \"<td style='vertical-align:middle;'>\";"
      puts "s += \"<div class='FooterButton' onclick='goStart()'  style='text-align:center;'>Zur&uuml;ck\";"
      puts "s += \"</div>\";"
      puts "s += \"</td>\";"
      puts "s += \"</tr>\";"
      puts "s += \"</tbody>\";"
      puts "s += \"</table>\";"
      puts "jQuery(\"#footer\").html(s);"
    }

    puts "goStart = function() \{"
    puts "window.location.href=\"$href\";"
    puts "\}"

    puts "loadExtHelp = function()\{"
    puts "  wndHelp = window.open(\"$HM_HELP_URL?lang=$LANGUAGE&vers=$ver(VERSION)&serial=$SERIAL\", \"Hilfe\", \"toolbar=yes,menubar=yes,location=yes,scrollbars=yes,resizable=yes,width=800,height=600\");"
    puts "\}"

    puts "translatePage('#overviewHelpPage');"
    puts "jQuery('#overviewHelpPage').css('display', 'table');"
  }
}


cgi_eval {
#cgi_debug -on
cgi_input
catch {
    import debug
    cgi_debug -on
}

set action "put_page"

http_head

catch { import action }
action_$action
}
