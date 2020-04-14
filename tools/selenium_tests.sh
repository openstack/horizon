# Uses envpython and toxinidir from tox run to construct a test command

test_results="--junitxml=${1}/test_reports/selenium_test_results.xml --html=${1}/test_reports/selenium_test_results.html"

pytest ${1}/openstack_dashboard/ --ds=openstack_dashboard.test.settings -v -m selenium $test_results --self-contained-html