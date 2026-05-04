# powershell script to explore the Enphase Envoy local API

# set this to whatever your Gateway's IP address is
$ipaddr="192.168.1.135"
# obtain an API key from https://entrez.enphaseenergy.com/ using your Enphase login details
$apikey="topsecretkey"

echo "info"
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/info

echo "ivp/ensemble/device_list"
# info on available devices, generally the Gateway and Battery
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/ivp/ensemble/device_list

echo "ivp/meters"
# info on the available meters, generally production and net-consumption
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/ivp/meters

echo "ivp/meters/readings"
# meter readings from each of the PV array (production), grid (net-consumption) and battery
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/ivp/meters/readings

echo "ivp/meters/gridReading"
# reports power being drawn/exported to each phase of the grid
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/ivp/meters/gridReading

echo "ivp/pdm/energy"
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/ivp/pdm/energy

echo "ivp/livedata/status"
# shows live status of grid, PV, battery and system load, in watts
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/ivp/livedata/status

echo "api/v1/production"
# shows PV production today, last 7 days, lifetime and instantaneously
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/api/v1/production

echo "api/v1/production/inverters"
# shows what each microinverter is doing
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/api/v1/production/inverters

echo "inventory"
# inventory of storage devices ie batteries
curl -f -k -H 'Accept: application/json' -H "Authorization: Bearer ${apikey}" -X GET https://$ipaddr/ivp/ensemble/inventory