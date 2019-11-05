#!/bin/bash


# Log output

    sudo mkdir -p logs;
    sudo chmod -R 0777 logs;
    exec &> >(tee -a "logs/${0##*/}_$(date +"%F").log") 2>&1;


# Collect data

    echo -e "\n\e[32mCollecting data\e[39m\n";

    read -p "Enter service name: " SName;
    if [ -z "$SName" ]; then echo "Exit: service name was empty"; exit; fi;
    echo;

    read -p "Enter service executable: " SEXE;
    if [ -z "$SEXE" ]; then echo "Exit: service executable was empty"; exit; fi;
    echo;

    read -p "Enter project name: " SLog;
    if [ -z "$SLog" ]; then echo "Exit: project name was empty"; exit; fi;
    echo;

    sudo tail -n 5 /etc/passwd;
    echo;
    read -p "Enter service ID (optional): " SID;
    echo;

    read -p "Enter deployment user (optional): " SDeploy;
    if [ -z "$SDeploy" ]; then SDeploy="tfsdeploy"; fi;
    echo;


# Create new user and set permissions

    echo -e "\n\e[32mCreating new user and setting permissions\e[39m\n";

    sudo sh -c "echo LC_ALL=\"en_US.UTF-8\" >> /etc/default/locale";

    sudo userdel $SName -f 2>/dev/null || :;
    sudo groupdel $SName -f 2>/dev/null || :;

    if [ -z "$SID" ]; then
        sudo useradd $SName -m -s /bin/false;
    else
        sudo useradd $SName -m -s /bin/false -u $SID;
    fi;
    sudo usermod -g $SDeploy $SName;

    sudo mkdir -p /home/$SName/app;
    sudo chown -R $SName:$SDeploy /home/$SName;
    sudo find /home/$SName -type f -exec sudo chmod 0664 {} \;
    sudo find /home/$SName -type d -exec sudo chmod 0775 {} \;


# Configure systemd from template

    echo -e "\n\e[32mConfiguring systemd\e[39m\n";

    echo "
[Unit]
Description=$SName

[Service]
WorkingDirectory=/home/$SName/app
ExecStart=/home/$SName/app/$SEXE
Restart=always
RestartSec=10
SyslogIdentifier=$SName
User=$SName
#Environment=ASPNETCORE_URLS=http://127.0.0.1:5000

[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/dotnet-$SName.service &>/dev/null;

    sudo systemctl reset-failed;
    sudo systemctl daemon-reload;
    sudo systemctl enable dotnet-$SName;
    sudo systemctl start dotnet-$SName;


# Configure rsyslog from template

    echo -e "\n\e[32mConfiguring rsyslog\e[39m\n";

    if [ ! -f "/etc/rsyslog.d/01-$SLog.conf" ]; then
        echo "template (name=\"rawdata\" type=\"string\" string=\"%msg%\n\")" | sudo tee /etc/rsyslog.d/01-$SLog.conf &>/dev/null;
    fi;

    if ! grep -q $SName "/etc/rsyslog.d/01-$SLog.conf"; then
        echo "if \$programname == '$SName' then { action(type=\"omfile\" file=\"/var/log/$SLog/$SName.log\" template=\"rawdata\") stop }" | sudo tee -a /etc/rsyslog.d/01-$SLog.conf &>/dev/null;
    fi;

    sudo systemctl restart rsyslog;

    sudo mkdir -p /var/log/$SLog;
    sudo chown -R syslog:www-data /var/log/$SLog;
    sudo chmod -R 0775 /var/log/$SLog;

    sudo systemctl restart rsyslog;


# Configure logrotate.d from template

    echo -e "\n\e[32mConfiguring logrotate\e[39m\n";

    echo "
/var/log/$SLog/*.log
{
    rotate 14
    daily
    missingok
    notifempty
    create 664
    compress
    delaycompress
    sharedscripts
    postrotate
    invoke-rc.d rsyslog rotate >/dev/null 2>&1 || true
    endscript
}
" | sudo tee /etc/logrotate.d/$SLog &>/dev/null;


# Change directory to systemd

    echo -e "\nEdit systemd manually if hosting web service!\n";
