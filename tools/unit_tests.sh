# Uses envpython and toxinidir from tox run to construct a test command
testcommand="pytest"
posargs="${@:2}"

tagarg="not selenium and not integration and not plugin_test"

# Attempt to identify if any of the arguments passed from tox is a test subset
if [ -n "$posargs" ]; then
  for arg in "$posargs"
  do
    if [ ${arg:0:1} != "-" ]; then
      subset=$arg
    fi
  done
fi

horizon_test_results="--junitxml=${1}/test_reports/horizon_test_results.xml --html=${1}/test_reports/horizon_test_results.html"
dashboard_test_results="--junitxml=${1}/test_reports/openstack_dashboard_test_results.xml --html=${1}/test_reports/openstack_dashboard_test_results.html"
auth_test_results="--junitxml=${1}/test_reports/openstack_auth_test_results.xml --html=${1}/test_reports/openstack_auth_test_results.html"
plugins_test_results="--junitxml=${1}/test_reports/plugin_test_results.xml --html=${1}/test_reports/plugin_test_results.html"
single_html="--self-contained-html"

# If we are running a test subset, supply the correct settings file.
# If not, simply run the entire test suite.
if [ -n "$subset" ]; then
  project="${subset%%/*}"
  if [ $project == "horizon" ]; then
    $testcommand $posargs --ds=horizon.test.settings -v -m "$tagarg" $horizon_test_results $single_html
  elif [ $project == "openstack_dashboard" ]; then
    $testcommand $posargs --ds=openstack_dashboard.test.settings -v -m "$tagarg" $dashboard_test_results $single_html
  elif [ $project == "openstack_auth" ]; then
    $testcommand $posargs --ds=openstack_auth.tests.settings -v -m "$tagarg" $auth_test_results $single_html
  elif [ $project == "plugin-test" ]; then
    $testcommand ${1}/openstack_dashboard/test/test_plugins --ds=openstack_dashboard.test.settings -v -m plugin_test $plugins_test_results $single_html
  fi
else
  $testcommand ${1}/horizon/ --ds=horizon.test.settings -v -m "$tagarg" $horizon_test_results $single_html
  horizon_tests=$?
  $testcommand ${1}/openstack_dashboard/ --ds=openstack_dashboard.test.settings -v -m "$tagarg" $dashboard_test_results $single_html
  openstack_dashboard_tests=$?
  $testcommand ${1}/openstack_auth/tests/ --ds=openstack_auth.tests.settings -v -m "$tagarg" $auth_test_results $single_html
  auth_tests=$?
  $testcommand ${1}/openstack_dashboard/ --ds=openstack_dashboard.test.settings -v -m plugin_test $plugins_test_results $single_html
  plugin_tests=$?
  # we have to tell tox if either of these test runs failed
  if [[ $horizon_tests != 0 || $openstack_dashboard_tests != 0 || \
    $auth_tests != 0 || $plugin_tests != 0 ]]; then
    exit 1;
  fi
fi
