
# NEP Inverters Local DNS Redirection Setup

This guide outlines the process for setting up a fake DNS server on a Raspberry Pi to redirect the domain `www.nepviewer.net` to a local server. This setup is intended for intercepting communication between NEP inverters and their default server.

## Setup Server and NEP Inverters

1. **Configure Your NEP Inverters:** Connect your NEP inverters to your Home WiFi network to ensure they are part of your local network and can communicate with your Raspberry Pi server.

## Setup a Fake DNS Server on Raspberry Pi

2. **Prepare Your Raspberry Pi:** Make sure your Raspberry Pi is set up with Raspberry Pi OS and connected to the same Home WiFi network as your NEP inverters. Assign a static IP address to your Raspberry Pi through your router's DHCP settings to prevent the IP address from changing.

3. **Install DNS Server Software:** Use `dnsmasq` for its simplicity and flexibility. Install it by running:
   ` sudo apt update && sudo apt install dnsmasq `

4. **Configure `dnsmasq`:** Create a fake DNS entry for `www.nepviewer.net` by editing the `dnsmasq` configuration.
   Backup the original configuration file:
   `sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.backup`
   Create a new configuration file with:
   `sudo nano /etc/dnsmasq.conf`
   Add the following lines, replacing `raspberry_pi_ip` with your Raspberry Pi’s IP address and `server_ip` with your server's IP address:
   `listen-address=127.0.0.1,raspberry_pi_ip
   address=/www.nepviewer.net/server_ip
   `

5. **Restart `dnsmasq` Service:** Apply the changes by restarting `dnsmasq`:
   `
   sudo systemctl restart dnsmasq
   `

6. **Update Your Devices:** Configure the DNS settings on your router or individual devices to use your Raspberry Pi’s IP as their primary DNS server. This ensures all DNS requests are routed through your Raspberry Pi.

## Verification

To verify the setup, use the `dig` command from another device on your network:
`
dig @raspberry_pi_ip www.nepviewer.net
`
Replace `raspberry_pi_ip` with your Raspberry Pi's IP address. The response should show your server's IP address as the answer.

## Done!