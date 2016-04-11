#!/bin/bash

set -o errexit

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Horizon's test suite(s)"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv.  Install automatically"
  echo "                           if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv.  Run tests in local"
  echo "                           environment"
  echo "  -c, --coverage           Generate reports using Coverage"
  echo "  -f, --force              Force a clean re-build of the virtual"
  echo "                           environment. Useful when dependencies have"
  echo "                           been added."
  echo "  -m, --manage             Run a Django management command."
  echo "  --makemessages           Create/Update English translation files."
  echo "  --compilemessages        Compile all translation files."
  echo "  --check-only             Do not update translation files (--makemessages only)."
  echo "  --pseudo                 Pseudo translate a language."
  echo "  -p, --pep8               Just run pep8"
  echo "  -8, --pep8-changed [<basecommit>]"
  echo "                           Just run PEP8 and HACKING compliance check"
  echo "                           on files changed since HEAD~1 (or <basecommit>)"
  echo "  -P, --no-pep8            Don't run pep8 by default"
  echo "  -t, --tabs               Check for tab characters in files."
  echo "  -y, --pylint             Just run pylint"
  echo "  -e, --eslint             Just run eslint"
  echo "  -k, --karma              Just run karma"
  echo "  -q, --quiet              Run non-interactively. (Relatively) quiet."
  echo "                           Implies -V if -N is not set."
  echo "  --only-selenium          Run only the Selenium unit tests"
  echo "  --with-selenium          Run unit tests including Selenium tests"
  echo "  --selenium-headless      Run Selenium tests headless"
  echo "  --selenium-phantomjs     Run Selenium tests using phantomjs (headless)"
  echo "  --integration            Run the integration tests (requires a running "
  echo "                           OpenStack environment)"
  echo "  --runserver              Run the Django development server for"
  echo "                           openstack_dashboard in the virtual"
  echo "                           environment."
  echo "  --docs                   Just build the documentation"
  echo "  --backup-environment     Make a backup of the environment on exit"
  echo "  --restore-environment    Restore the environment before running"
  echo "  --destroy-environment    Destroy the environment and exit"
  echo "  -h, --help               Print this usage message"
  echo ""
  echo "Note: with no options specified, the script will try to run the tests in"
  echo "  a virtual environment,  If no virtualenv is found, the script will ask"
  echo "  if you would like to create one.  If you prefer to run tests NOT in a"
  echo "  virtual environment, simply pass the -N option."
  exit
}

# DEFAULTS FOR RUN_TESTS.SH
#
root=`pwd -P`
venv=$root/.venv
venv_env_version=$venv/environments
with_venv=tools/with_venv.sh
included_dirs="openstack_dashboard horizon"

always_venv=0
backup_env=0
command_wrapper=""
destroy=0
force=0
just_pep8=0
just_pep8_changed=0
no_pep8=0
just_pylint=0
just_docs=0
just_tabs=0
just_eslint=0
just_karma=0
never_venv=0
quiet=0
restore_env=0
runserver=0
only_selenium=0
with_selenium=0
selenium_headless=0
selenium_phantomjs=0
integration=0
testopts=""
testargs=""
with_coverage=0
makemessages=0
compilemessages=0
check_only=0
pseudo=0
manage=0

# Jenkins sets a "JOB_NAME" variable, if it's not set, we'll make it "default"
[ "$JOB_NAME" ] || JOB_NAME="default"

function process_option {
  # If running manage command, treat the rest of options as arguments.
  if [ $manage -eq 1 ]; then
     testargs="$testargs $1"
     return 0
  fi

  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) always_venv=1; never_venv=0;;
    -N|--no-virtual-env) always_venv=0; never_venv=1;;
    -p|--pep8) just_pep8=1;;
    -8|--pep8-changed) just_pep8_changed=1;;
    -P|--no-pep8) no_pep8=1;;
    -y|--pylint) just_pylint=1;;
    -e|--eslint) just_eslint=1;;
    -k|--karma) just_karma=1;;
    -f|--force) force=1;;
    -t|--tabs) just_tabs=1;;
    -q|--quiet) quiet=1;;
    -c|--coverage) with_coverage=1;;
    -m|--manage) manage=1;;
    --makemessages) makemessages=1;;
    --compilemessages) compilemessages=1;;
    --check-only) check_only=1;;
    --pseudo) pseudo=1;;
    --only-selenium) only_selenium=1;;
    --with-selenium) with_selenium=1;;
    --selenium-headless) selenium_headless=1;;
    --selenium-phantomjs) selenium_phantomjs=1;;
    --integration) integration=1;;
    --docs) just_docs=1;;
    --runserver) runserver=1;;
    --backup-environment) backup_env=1;;
    --restore-environment) restore_env=1;;
    --destroy-environment) destroy=1;;
    -*) testopts="$testopts $1";;
    *) testargs="$testargs $1"
  esac
}

function run_management_command {
  ${command_wrapper} python $root/manage.py $testopts $testargs
}

function run_server {
  echo "Starting Django development server..."
  ${command_wrapper} python $root/manage.py runserver $testopts $testargs
  echo "Server stopped."
}

function run_pylint {
  echo "Running pylint ..."
  PYTHONPATH=$root ${command_wrapper} pylint --rcfile=.pylintrc -f parseable $included_dirs > pylint.txt || true
  CODE=$?
  grep Global -A2 pylint.txt
  if [ $CODE -lt 32 ]; then
      echo "Completed successfully."
      exit 0
  else
      echo "Completed with problems."
      exit $CODE
  fi
}

function run_eslint {
  echo "Running eslint ..."
  if [ "`which npm`" == '' ] ; then
    echo "npm is not present; please install, e.g. sudo apt-get install npm"
  else
    npm install
    npm run lint
  fi
}

function run_karma {
  echo "Running karma ..."
  npm install
  npm run test
}

function warn_on_flake8_without_venv {
  set +o errexit
  ${command_wrapper} python -c "import hacking" 2>/dev/null
  no_hacking=$?
  set -o errexit
  if [ $never_venv -eq 1 -a $no_hacking -eq 1 ]; then
      echo "**WARNING**:" >&2
      echo "OpenStack hacking is not installed on your host. Its detection will be missed." >&2
      echo "Please install or use virtual env if you need OpenStack hacking detection." >&2
  fi
}

function run_pep8 {
  echo "Running flake8 ..."
  warn_on_flake8_without_venv
  DJANGO_SETTINGS_MODULE=openstack_dashboard.test.settings ${command_wrapper} flake8
}

function run_pep8_changed {
    # NOTE(gilliard) We want use flake8 to check the entirety of every file that has
    # a change in it. Unfortunately the --filenames argument to flake8 only accepts
    # file *names* and there are no files named (eg) "nova/compute/manager.py".  The
    # --diff argument behaves surprisingly as well, because although you feed it a
    # diff, it actually checks the file on disk anyway.
    local base_commit=${testargs:-HEAD~1}
    files=$(git diff --name-only $base_commit | tr '\n' ' ')
    echo "Running flake8 on ${files}"
    warn_on_flake8_without_venv
    diff -u --from-file /dev/null ${files} | DJANGO_SETTINGS_MODULE=openstack_dashboard.test.settings ${command_wrapper} flake8 --diff
    exit
}

function run_sphinx {
    echo "Building sphinx..."
    DJANGO_SETTINGS_MODULE=openstack_dashboard.test.settings ${command_wrapper} python setup.py build_sphinx
    echo "Build complete."
}

function tab_check {
  TAB_VIOLATIONS=`find $included_dirs -type f -regex ".*\.\(css\|js\|py\|html\)" -print0 | xargs -0 awk '/\t/' | wc -l`
  if [ $TAB_VIOLATIONS -gt 0 ]; then
    echo "TABS! $TAB_VIOLATIONS of them! Oh no!"
    HORIZON_FILES=`find $included_dirs -type f -regex ".*\.\(css\|js\|py|\html\)"`
    for TABBED_FILE in $HORIZON_FILES
    do
      TAB_COUNT=`awk '/\t/' $TABBED_FILE | wc -l`
      if [ $TAB_COUNT -gt 0 ]; then
        echo "$TABBED_FILE: $TAB_COUNT"
      fi
    done
  fi
  return $TAB_VIOLATIONS;
}

function destroy_venv {
  echo "Cleaning environment..."
  echo "Removing virtualenv..."
  rm -rf $venv
  echo "Virtualenv removed."
}

function environment_check {
  echo "Checking environment."
  if [ -f $venv_env_version ]; then
    set +o errexit
    cat requirements.txt test-requirements.txt | cmp $venv_env_version - > /dev/null
    local env_check_result=$?
    set -o errexit
    if [ $env_check_result -eq 0 ]; then
      # If the environment exists and is up-to-date then set our variables
      command_wrapper="${root}/${with_venv}"
      echo "Environment is up to date."
      return 0
    fi
  fi

  if [ $always_venv -eq 1 ]; then
    install_venv
  else
    if [ ! -e ${venv} ]; then
      echo -e "Environment not found. Install? (Y/n) \c"
    else
      echo -e "Your environment appears to be out of date. Update? (Y/n) \c"
    fi
    read update_env
    if [ "x$update_env" = "xY" -o "x$update_env" = "x" -o "x$update_env" = "xy" ]; then
      install_venv
    else
      # Set our command wrapper anyway.
      command_wrapper="${root}/${with_venv}"
    fi
  fi
}

function sanity_check {
  # Anything that should be determined prior to running the tests, server, etc.
  # Don't sanity-check anything environment-related in -N flag is set
  if [ $never_venv -eq 0 ]; then
    if [ ! -e ${venv} ]; then
      echo "Virtualenv not found at $venv. Did install_venv.py succeed?"
      exit 1
    fi
  fi
  # Remove .pyc files. This is sanity checking because they can linger
  # after old files are deleted.
  find . -name "*.pyc" -exec rm -rf {} \;
}

function backup_environment {
  if [ $backup_env -eq 1 ]; then
    echo "Backing up environment \"$JOB_NAME\"..."
    if [ ! -e ${venv} ]; then
      echo "Environment not installed. Cannot back up."
      return 0
    fi
    if [ -d /tmp/.horizon_environment/$JOB_NAME ]; then
      mv /tmp/.horizon_environment/$JOB_NAME /tmp/.horizon_environment/$JOB_NAME.old
      rm -rf /tmp/.horizon_environment/$JOB_NAME
    fi
    mkdir -p /tmp/.horizon_environment/$JOB_NAME
    cp -r $venv /tmp/.horizon_environment/$JOB_NAME/
    # Remove the backup now that we've completed successfully
    rm -rf /tmp/.horizon_environment/$JOB_NAME.old
    echo "Backup completed"
  fi
}

function restore_environment {
  if [ $restore_env -eq 1 ]; then
    echo "Restoring environment from backup..."
    if [ ! -d /tmp/.horizon_environment/$JOB_NAME ]; then
      echo "No backup to restore from."
      return 0
    fi

    cp -r /tmp/.horizon_environment/$JOB_NAME/.venv ./ || true
    echo "Environment restored successfully."
  fi
}

function install_venv {
  # Install with install_venv.py
  export PIP_DOWNLOAD_CACHE=${PIP_DOWNLOAD_CACHE-/tmp/.pip_download_cache}
  export PIP_USE_MIRRORS=true
  if [ $quiet -eq 1 ]; then
    export PIP_NO_INPUT=true
  fi
  echo "Fetching new src packages..."
  rm -rf $venv/src
  python tools/install_venv.py
  command_wrapper="$root/${with_venv}"
  # Make sure it worked and record the environment version
  sanity_check
  chmod -R 754 $venv
  cat requirements.txt test-requirements.txt > $venv_env_version
}

function run_tests {
  sanity_check

  if [ $with_selenium -eq 1 ]; then
    export WITH_SELENIUM=1
  elif [ $only_selenium -eq 1 ]; then
    export WITH_SELENIUM=1
    export SKIP_UNITTESTS=1
  fi

  if [ $with_selenium -eq 0 -a $integration -eq 0 ]; then
      testopts="$testopts --exclude-dir=openstack_dashboard/test/integration_tests"
  fi

  if [ $selenium_headless -eq 1 ]; then
    export SELENIUM_HEADLESS=1
  fi

  if [ $selenium_phantomjs -eq 1 ]; then
    export SELENIUM_PHANTOMJS=1
  fi

  if [ -z "$testargs" ]; then
     run_tests_all
  else
     run_tests_subset
  fi
}

function run_tests_subset {
  project=`echo $testargs | awk -F. '{print $1}'`
  ${command_wrapper} python $root/manage.py test --settings=$project.test.settings $testopts $testargs
}

function run_tests_all {
  echo "Running Horizon application tests"
  export NOSE_XUNIT_FILE=horizon/nosetests.xml
  if [ "$NOSE_WITH_HTML_OUTPUT" = '1' ]; then
    export NOSE_HTML_OUT_FILE='horizon_nose_results.html'
  fi
  if [ $with_coverage -eq 1 ]; then
    ${command_wrapper} python -m coverage.__main__ erase
    coverage_run="python -m coverage.__main__ run -p"
  fi
  ${command_wrapper} ${coverage_run} $root/manage.py test horizon --settings=horizon.test.settings $testopts
  # get results of the Horizon tests
  HORIZON_RESULT=$?

  echo "Running openstack_dashboard tests"
  export NOSE_XUNIT_FILE=openstack_dashboard/nosetests.xml
  if [ "$NOSE_WITH_HTML_OUTPUT" = '1' ]; then
    export NOSE_HTML_OUT_FILE='dashboard_nose_results.html'
  fi
  ${command_wrapper} ${coverage_run} $root/manage.py test openstack_dashboard --settings=openstack_dashboard.test.settings $testopts
  # get results of the openstack_dashboard tests
  DASHBOARD_RESULT=$?

  if [ $with_coverage -eq 1 ]; then
    echo "Generating coverage reports"
    ${command_wrapper} python -m coverage.__main__ combine
    ${command_wrapper} python -m coverage.__main__ xml -i --include="horizon/*,openstack_dashboard/*" --omit='/usr*,setup.py,*egg*,.venv/*'
    ${command_wrapper} python -m coverage.__main__ html -i --include="horizon/*,openstack_dashboard/*" --omit='/usr*,setup.py,*egg*,.venv/*' -d reports
  fi
  # Remove the leftover coverage files from the -p flag earlier.
  rm -f .coverage.*

  PEP8_RESULT=0
  if [ $no_pep8 -eq 0 ] && [ $only_selenium -eq 0 ]; then
      run_pep8
      PEP8_RESULT=$?
  fi

  TEST_RESULT=$(($HORIZON_RESULT || $DASHBOARD_RESULT || $PEP8_RESULT))
  if [ $TEST_RESULT -eq 0 ]; then
    echo "Tests completed successfully."
  else
    echo "Tests failed."
  fi
  exit $TEST_RESULT
}

function run_integration_tests {
  export INTEGRATION_TESTS=1

  if [ $selenium_headless -eq 1 ]; then
    export SELENIUM_HEADLESS=1
  fi

  if [ $selenium_phantomjs -eq 1 ]; then
    export SELENIUM_PHANTOMJS=1
  fi

  echo "Running Horizon integration tests..."
  if [ -z "$testargs" ]; then
      ${command_wrapper} nosetests openstack_dashboard/test/integration_tests/tests
  else
      ${command_wrapper} nosetests $testargs
  fi
  exit 0
}

function babel_extract {
  local MODULE_NAME=$1
  local DOMAIN=$2
  local KEYWORDS="-k gettext_noop -k gettext_lazy -k ngettext_lazy:1,2"
  KEYWORDS+=" -k ugettext_noop -k ugettext_lazy -k ungettext_lazy:1,2"
  KEYWORDS+=" -k npgettext:1c,2,3 -k pgettext_lazy:1c,2 -k npgettext_lazy:1c,2,3"

  ${command_wrapper} pybabel extract -F babel-${DOMAIN}.cfg \
      --add-comments Translators: -o $MODULE_NAME/locale/${DOMAIN}.pot \
      $KEYWORDS $MODULE_NAME
}

function run_makemessages {

  echo -n "horizon: "
  babel_extract horizon django
  HORIZON_PY_RESULT=$?

  echo -n "horizon javascript: "
  babel_extract horizon djangojs
  HORIZON_JS_RESULT=$?

  echo -n "openstack_dashboard: "
  babel_extract openstack_dashboard django
  DASHBOARD_RESULT=$?

  echo -n "openstack_dashboard javascript: "
  babel_extract openstack_dashboard djangojs
  DASHBOARD_JS_RESULT=$?

  if [ $check_only -eq 1 ]; then
    git checkout -- horizon/locale/django*.pot
    git checkout -- openstack_dashboard/locale/django*.pot
  fi

  exit $(($HORIZON_PY_RESULT || $HORIZON_JS_RESULT || $DASHBOARD_RESULT || $DASHBOARD_JS_RESULT))
}

function run_compilemessages {
  cd horizon
  ${command_wrapper} $root/manage.py compilemessages
  HORIZON_PY_RESULT=$?
  cd ../openstack_dashboard
  ${command_wrapper} $root/manage.py compilemessages
  DASHBOARD_RESULT=$?
  exit $(($HORIZON_PY_RESULT || $DASHBOARD_RESULT))
}

function run_pseudo {
  for lang in $testargs
  # Use English pot file as the source file/pot file just like real Horizon translations
  do
      ${command_wrapper} $root/tools/pseudo.py openstack_dashboard/locale/django.pot openstack_dashboard/locale/$lang/LC_MESSAGES/django.po $lang
      ${command_wrapper} $root/tools/pseudo.py openstack_dashboard/locale/djangojs.pot openstack_dashboard/locale/$lang/LC_MESSAGES/djangojs.po $lang
      ${command_wrapper} $root/tools/pseudo.py horizon/locale/django.pot horizon/locale/$lang/LC_MESSAGES/django.po $lang
      ${command_wrapper} $root/tools/pseudo.py horizon/locale/djangojs.pot horizon/locale/$lang/LC_MESSAGES/djangojs.po $lang
  done
  exit $?
}


# ---------PREPARE THE ENVIRONMENT------------ #

# PROCESS ARGUMENTS, OVERRIDE DEFAULTS
for arg in "$@"; do
    process_option $arg
done

if [ $quiet -eq 1 ] && [ $never_venv -eq 0 ] && [ $always_venv -eq 0 ]
then
  always_venv=1
fi

# If destroy is set, just blow it away and exit.
if [ $destroy -eq 1 ]; then
  destroy_venv
  exit 0
fi

# Ignore all of this if the -N flag was set
if [ $never_venv -eq 0 ]; then

  # Restore previous environment if desired
  if [ $restore_env -eq 1 ]; then
    restore_environment
  fi

  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    destroy_venv
  fi

  # Then check if it's up-to-date
  environment_check

  # Create a backup of the up-to-date environment if desired
  if [ $backup_env -eq 1 ]; then
    backup_environment
  fi
fi

# ---------EXERCISE THE CODE------------ #

# Run management commands
if [ $manage -eq 1 ]; then
    run_management_command
    exit $?
fi

# Build the docs
if [ $just_docs -eq 1 ]; then
    run_sphinx
    exit $?
fi

# Update translation files
if [ $makemessages -eq 1 ]; then
    run_makemessages
    exit $?
fi

# Compile translation files
if [ $compilemessages -eq 1 ]; then
    run_compilemessages
    exit $?
fi

# Generate Pseudo translation
if [ $pseudo -eq 1 ]; then
    run_pseudo
    exit $?
fi

# PEP8
if [ $just_pep8 -eq 1 ]; then
    run_pep8
    exit $?
fi

if [ $just_pep8_changed -eq 1 ]; then
    run_pep8_changed
    exit $?
fi

# Pylint
if [ $just_pylint -eq 1 ]; then
    run_pylint
    exit $?
fi

# ESLint
if [ $just_eslint -eq 1 ]; then
    run_eslint
    exit $?
fi

# Karma
if [ $just_karma -eq 1 ]; then
    run_karma
    exit $?
fi

# Tab checker
if [ $just_tabs -eq 1 ]; then
    tab_check
    exit $?
fi

# Integration tests
if [ $integration -eq 1 ]; then
    run_integration_tests
    exit $?
fi

# Django development server
if [ $runserver -eq 1 ]; then
    run_server
    exit $?
fi

# Full test suite
run_tests || exit
