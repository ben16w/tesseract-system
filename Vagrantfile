# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"

  config.ssh.insert_key = false

  config.vm.network "private_network", ip: "192.168.56.11"

  config.vm.synced_folder ".", "/vagrant_data", disabled: true

  config.vm.disk :disk, name: "disk1", size: "4GB"
  config.vm.disk :disk, name: "disk2", size: "4GB"
  config.vm.disk :disk, name: "parity1", size: "4GB"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"
  end

  config.vm.provision "shell", privileged: true, inline: <<-SHELL
    if [ ! -f /provisioned ]; then
      apt-get update
      DEBIAN_FRONTEND=noninteractive apt-get -yq install cryptsetup python3-setuptools python3-pip unzip git zip

      function setup_disk {

        if [ -e "/dev/disk/by-uuid/${1}" ]; then
          echo "Disk found, skipping"
          return
        fi

        mkdir /media/${3}
        echo 'type=83' | sfdisk "/dev/${2}"
        echo -n "password" | cryptsetup -q luksFormat "/dev/${2}1" -
        echo -n "password" | cryptsetup luksOpen "/dev/${2}1" "luks-${1}" -
        mkfs.ext4 "/dev/mapper/luks-${1}" -U "${1}"
        echo -n "YES\n" | cryptsetup luksUUID /dev/${2}1 --uuid "${1}"
        mount "/dev/mapper/luks-${1}" "/media/${3}"

        # massive bodge but the whole script is tbf
        if [ "${3}" != "parity1" ]; then
          for i in {1..10}; do
            dd if=/dev/urandom bs=1M count=8 of="/media/${3}/testfile-${2}1-$i"
            chmod 777 "/media/${3}/testfile-${2}1-$i"
            chown 1000:1000 "/media/${3}/testfile-${2}1-$i"
          done
        fi

        umount "/media/${3}"
        cryptsetup luksClose "/dev/mapper/luks-${1}"
        rm -rf /media/${3}

      }

      setup_disk 1d60fef0-761a-4d73-99ca-83c2e3de58e4 sdb disk1
      setup_disk 0133f767-9b68-461a-9acd-61327358f725 sdc disk2
      setup_disk 229232cf-1a42-4a0d-af06-fc407b0587f6 sdd parity1

      touch /provisioned
    else
      echo "Already provisioned"
    fi
  SHELL

end