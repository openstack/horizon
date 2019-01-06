# Uses envpython and toxinidir from tox run to construct a test command
testcommand="${1} ${2}/manage.py test"
posargs="${@:3}"

tagarg="--exclude-tag selenium --exclude-tag integration --exclude-tag plugin-test"

if [[ -n "${WITH_SELENIUM}" ]]
then
  tagarg="--tag selenium"
elif [[ -n "${INTEGRATION_TESTS}" ]]
then
  tagarg="--tag integration"
#else
#  tag="unit"
fi

# Attempt to identify if any of the arguments passed from tox is a test subset
if [ -n "$posargs" ]; then
  for arg in "$posargs"
  do
    if [ ${arg:0:1} != "-" ]; then
      subset=$arg
    fi
  done
fi

# If we are running a test subset, supply the correct settings file.
# If not, simply run the entire test suite.
if [ -n "$subset" ]; then
  project="${subset%%.*}"
  if [ $project == "horizon" ]; then
    $testcommand --settings=horizon.test.settings --verbosity 2 $tagarg $posargs
  elif [ $project == "openstack_dashboard" ]; then
    $testcommand --settings=openstack_dashboard.test.settings --verbosity 2 $tagarg $posargs
  elif [ $project == "openstack_auth" ]; then
    $testcommand --settings=openstack_auth.tests.settings --verbosity 2 $tagarg $posargs
  elif [ $project == "plugin-test" ]; then
    $testcommand --settings=openstack_dashboard.test.settings --verbosity 2 --tag plugin-test openstack_dashboard.test.test_plugins
  fi
else
  $testcommand horizon --settings=horizon.test.settings --verbosity 2 $tagarg $posargs
  horizon_tests=$?
  $testcommand openstack_dashboard --settings=openstack_dashboard.test.settings --verbosity 2 $tagarg $posargs
  openstack_dashboard_tests=$?
  $testcommand openstack_auth --settings=openstack_auth.tests.settings --verbosity 2 $tagarg $posargs
  auth_tests=$?
  $testcommand --settings=openstack_dashboard.test.settings --verbosity 2 --tag plugin-test openstack_dashboard.test.test_plugins
  plugin_tests=$?
  # we have to tell tox if either of these test runs failed
  if [[ $horizon_tests != 0 || $openstack_dashboard_tests != 0 || \
    $auth_tests != 0 || $plugin_tests != 0 ]]; then
    exit 1;
  fi
fi
