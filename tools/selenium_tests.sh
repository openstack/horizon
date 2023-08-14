ROOT=$1

report_args="--junitxml=$ROOT/test_reports/selenium_test_results.xml"
report_args+=" --html=$ROOT/test_reports/selenium_test_results.html"
report_args+=" --self-contained-html"
ignore="--ignore=$ROOT/openstack_dashboard/test/selenium"

pytest $ROOT/openstack_dashboard/ --ds=openstack_dashboard.test.settings $ignore -v -m selenium $report_args
