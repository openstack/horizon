# Usage: unit_tests.sh [--coverage] <root_dir> [<test-file>, ...]

if [ "$1" = "--coverage" ]; then
  shift
  coverage=1
else
  coverage=0
fi

root=$1
posargs="${@:2}"

report_dir=$root/test_reports

# Attempt to identify if any of the arguments passed from tox is a test subset
if [ -n "$posargs" ]; then
  for arg in "$posargs"
  do
    if [ ${arg:0:1} != "-" ]; then
      subset=$arg
    fi
  done
fi


function run_test {
  local project=$1
  local tag
  local target
  local settings_module
  local report_args

  tag="not selenium and not integration and not plugin_test"

  case "$project" in
    horizon)
      settings_module="horizon.test.settings"
      ;;
    openstack_dashboard)
      settings_module="openstack_dashboard.test.settings"
      ;;
    openstack_auth)
      settings_module="openstack_auth.tests.settings"
      ;;
    plugin|plugin-test|plugin_test)
      project="plugin"
      tag="plugin_test"
      target="$root/openstack_dashboard/test/test_plugins"
      settings_module="openstack_dashboard.test.settings"
      ;;
    *)
      # Declare error by returning 1 which usually means error in bash
      return 1
  esac

  if [ -z "$target" ]; then
    if [ -n "$subset" ]; then
      target="$subset"
    else
      target="$root/$project"
    fi
  fi

  if [ "$coverage" -eq 1 ]; then
    coverage run -m pytest $target --ds=$settings_module -m "$tag"
  else
    report_args="--junitxml=$report_dir/${project}_test_results.xml"
    report_args+=" --html=$report_dir/${project}_test_results.html"
    report_args+=" --self-contained-html"

    pytest $target --ds=$settings_module -v -m "$tag" $report_args
  fi
  return $?
}

# If we are running a test subset, supply the correct settings file.
# If not, simply run the entire test suite.
if [ -n "$subset" ]; then
  project="${subset%%/*}"
  run_test $project
  exit $?
else
  results=()
  for project in horizon openstack_dashboard openstack_auth plugin; do
    run_test $project
    results+=($?)
  done

  # we have to tell tox if either of these test runs failed
  for r in "${results[@]}"; do
    if [ $r != 0 ]; then
      exit 1
    fi
  done
fi
