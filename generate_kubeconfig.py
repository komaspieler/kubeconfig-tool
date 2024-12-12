import json
import yaml
import os.path
import os
import subprocess
from pick import pick
from pathlib import Path
from configparser import ConfigParser

## TODO: add support for multiple users per cluster
## TODO: add configurable region support

# Verify AWS Config File Exists
aws_config_file = Path(os.path.expanduser("~/.aws/config"))
print("Checking whether {} exists..".format(aws_config_file), end='')

if aws_config_file.exists():
	print("OK")

	# Prepare AWS Config
	print("Loading AWS CLI Configuration..", end='')
	try:
		config = ConfigParser(allow_no_value=True)
		config.read_file(aws_config_file.open())
		print("OK")
	except:
		print("ERR")
		exit()

# Get List of Accounts
print("Retrieving list of available profiles..", end='')
try:
	result = subprocess.run(["aws configure list-profiles"], shell=True, capture_output = True, text = True)
	profiles = result.stdout.splitlines()

	print("Found {} profile(s)".format(len(profiles)))
except:
	print("ERR: {}".format(result.stderr))
	exit()

title = "Select the profile for which you wish to import the kubeconfig"
profile, index = pick(profiles, title)
print("Selected profile: {}..".format(profile))

print("Looking for clusters..", end='')
try:
	result = subprocess.run(["aws eks list-clusters  --profile {} --region eu-central-1 --output json --no-cli-pager".format(profile)], shell=True, capture_output = True, text = True)
	clusters = json.loads(result.stdout)['clusters']

	print("Found {} cluster(s)".format(len(clusters)))
except:
	print("ERR: {}".format(result.stderr))
	exit()

title = "Select the cluster which you would like to configure"
cluster, index = pick(clusters, title)
print("Selected cluster: {}".format(cluster))

print("\n\nALIAS CONFIG\nEnter an alias you want to use (default: {})".format(cluster))
alias = input()

# run aws update-kubeconfig
try:
	result = subprocess.run(["aws eks update-kubeconfig --name {} --alias {} --region eu-central-1 --profile {}".format(cluster, alias, profile)], shell=True, text = True)
	# result = os.system("source assume {} && aws eks update-kubeconfig --name {} --alias {} --profile {}".format(profile, cluster, alias, profile))
	print("OK")
except:
	print("ERR: {}".format(result.stderr))
	exit()


# Verify kube Config File Exists
kube_config_file = Path(os.path.expanduser("~/.kube/config"))
print("Checking whether {} exists..".format(kube_config_file), end='')

if kube_config_file.exists():
	print("OK")

	# Prepare kube Config
	print("Loading {} Configuration..".format(kube_config_file), end='')
	try:
		kubeconfigfile = kube_config_file.open(mode='r+')
		kubeconfig = yaml.safe_load(kubeconfigfile)
		print("OK")
	except:
		print("ERR")
		exit()


# get cluster arn
cluster_arn = [context['context']['cluster'] for context in kubeconfig['contexts'] if context['name'] == alias][0]

# generate granted config
granted_exec = {
	'apiVersion': "client.authentication.k8s.io/v1beta1",
	'args': [profile, "--exec", "aws --region eu-central-1 eks get-token --cluster-name {}".format(cluster)],
	'command': "assume",
	'env': [
		{
			'name': "GRANTED_QUIET",
			'value': "true"
		},
		{
			'name': "FORCE_NO_ALIAS",
			'value': "true"
		}
	],
	'interactiveMode': "IfAvailable",
	'provideClusterInfo': False
}

# modify user
print("Modifying user..", end='')
try:
	users = kubeconfig['users']
	user = [usr for usr in users if usr['name'] == cluster_arn][0]
	user['user']['exec'] = granted_exec
	kubeconfig['users'] = [user if usr['name'] == cluster_arn else usr for usr in users]
	print("OK")
except:
	print("ERR")
	exit()

# write to file
print("Updating {}..".format(kube_config_file), end='')
try:
	kubeconfigfile = kube_config_file.open(mode='w')
	yaml.dump(kubeconfig, kubeconfigfile)
	print("OK")
except:
	print("ERR")
	exit()

print("ALL DONE")