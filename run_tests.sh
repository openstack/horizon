#!/bin/bash

set -o errexit

# ---------------UPDATE ME-------------------------------#
# Increment me any time the environment should be rebuilt.
# This includes dependncy changes, directory renames, etc.
# Simple integer secuence: 1, 2, 3...
environment_version=6
#--------------------------------------------------------#

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
  echo "  -p, --pep8               Just run pep8"
  echo "  -t, --tabs               Check for tab characters in files."
  echo "  -y, --pylint             Just run pylint"
  echo "  -q, --quiet              Run non-interactively. (Relatively) quiet."
  echo "                           Implies -V if -N is not set."
  echo "  --with-selenium          Run unit tests including Selenium tests"
  echo "  --runserver              Run the Django development server for"
  echo "                           openstack-dashboard in the virtual"
  echo "                           environment."
  echo "  --docs                   Just build the documentation"
  echo "  --backup-environment     Make a backup of the environment on exit"
  echo "  --restore-environment    Restore the environment before running"
  echo "  --destroy-environment    DEstroy the environment and exit"
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
venv=openstack-dashboard/.dashboard-venv
django_with_venv=openstack-dashboard/tools/with_venv.sh
dashboard_with_venv=tools/with_venv.sh
always_venv=0
never_venv=0
force=0
with_coverage=0
selenium=0
testargs=""
django_wrapper=""
dashboard_wrapper=""
just_pep8=0
just_pylint=0
just_docs=0
just_tabs=0
runserver=0
quiet=0
backup_env=0
restore_env=0
destroy=0

# Jenkins sets a "JOB_NAME" variable, if it's not set, we'll make it "default"
[ "$JOB_NAME" ] || JOB_NAME="default"

function process_option {
  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) always_venv=1; never_venv=0;;
    -N|--no-virtual-env) always_venv=0; never_venv=1;;
    -p|--pep8) just_pep8=1;;
    -y|--pylint) just_pylint=1;;
    -f|--force) force=1;;
    -t|--tabs) just_tabs=1;;
    -q|--quiet) quiet=1;;
    -c|--coverage) with_coverage=1;;
    --with-selenium) selenium=1;;
    --docs) just_docs=1;;
    --runserver) runserver=1;;
    --backup-environment) backup_env=1;;
    --restore-environment) restore_env=1;;
    --destroy-environment) destroy=1;;
    *) testargs="$testargs $1"
  esac
}

function run_server {
  echo "Starting Django development server..."
  ${django_wrapper} python openstack-dashboard/dashboard/manage.py runserver $testargs
  echo "Server stopped."
}

function run_pylint {
  echo "Running pylint ..."
  PYLINT_INCLUDE="openstack-dashboard/dashboard horizon/horizon"
  ${django_wrapper} pylint --rcfile=.pylintrc -f parseable $PYLINT_INCLUDE > pylint.txt || true
  CODE=$?
  grep Global -A2 pylint.txt
  if [ $CODE -lt 32 ]
  then
      echo "Completed successfully."
      exit 0
  else
      echo "Completed with problems."
      exit $CODE
  fi
}

function run_pep8 {
  echo "Running pep8 ..."
  rm -f pep8.txt
  PEP8_EXCLUDE=vcsversion.py
  PEP8_OPTIONS="--exclude=$PEP8_EXCLUDE --repeat"
  PEP8_INCLUDE="openstack-dashboard/dashboard horizon/horizon"
  echo "${django_wrapper} pep8 $PEP8_OPTIONS $PEP8_INCLUDE > pep8.txt"
  ${django_wrapper} pep8 $PEP8_OPTIONS $PEP8_INCLUDE | perl -ple 's/: ([WE]\d+)/: [$1]/' > pep8.txt || true
  PEP8_COUNT=`wc -l pep8.txt | awk '{ print $1 }'`
  if [ $PEP8_COUNT -ge 1 ]; then
    echo "PEP8 violations found ($PEP8_COUNT):"
    cat pep8.txt
    echo "Please fix all PEP8 violations before committing."
  else
    echo "No violations found. Good job!"
  fi
}

function run_sphinx {
    echo "Building sphinx..."
    echo "export DJANGO_SETTINGS_MODULE=dashboard.settings"
    export DJANGO_SETTINGS_MODULE=dashboard.settings
    echo "${django_wrapper} sphinx-build -b html docs/source docs/build/html"
    ${django_wrapper} sphinx-build -b html docs/source docs/build/html
    echo "Build complete."
}

function tab_check {
  TAB_VIOLATIONS=`find horizon/horizon openstack-dashboard/dashboard -type f -regex ".*\.\(css\|js\|py\|html\)" -print0 | xargs -0 awk '/\t/' | wc -l`
  if [ $TAB_VIOLATIONS -gt 0 ]; then
    echo "TABS! $TAB_VIOLATIONS of them! Oh no!"
    HORIZON_FILES=`find horizon/horizon openstack-dashboard/dashboard -type f -regex ".*\.\(css\|js\|py|\html\)"`
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

function destroy_buildout {
  echo "Removing buildout files..."
  rm -rf horizon/bin
  rm -rf horizon/eggs
  rm -rf horizon/parts
  rm -rf horizon/develop-eggs
  rm -rf horizon/horizon.egg-info
  echo "Buildout files removed."
}

function destroy_venv {
  echo "Cleaning virtualenv..."
  destroy_buildout
  echo "Removing virtualenv..."
  rm -rf openstack-dashboard/.dashboard-venv
  echo "Virtualenv removed."
  rm -f .environment_version
  echo "Environment cleaned."
}

function environment_check {
  echo "Checking environment."
  if [ -f .environment_version ]; then
    ENV_VERS=`cat .environment_version`
    if [ $ENV_VERS -eq $environment_version ]; then
      if [ -e ${venv} ]; then
        # If the environment exists and is up-to-date then set our variables
        django_wrapper="${django_with_venv}"
        dashboard_wrapper="${dashboard_with_venv}"
        echo "Environment is up to date."
        return 0
      fi
    fi
  fi

  if [ $always_venv -eq 1 ]; then
    destroy_buildout
    install_venv
  else
    if [ ! -e ${venv} ]; then
      echo -e "Environment not found. Install? (Y/n) \c"
    else
      echo -e "Your environment appears to be out of date. Update? (Y/n) \c"
    fi
    read update_env
    if [ "x$update_env" = "xY" -o "x$update_env" = "x" -o "x$update_env" = "xy" ]; then
      # Buildout doesn't play nice with upgrading everytime; kill it to be safe
      destroy_buildout
      install_venv
    fi
  fi
}

function sanity_check {
  # Anything that should be determined prior to running the tests, server, etc.
  # Don't sanity-check anything environment-related in -N flag is set
  if [ $never_venv -eq 0 ]; then
    if [ ! -e ${venv} ]; then
      echo "Virtualenv not found at openstack-dashboard/.dashboard-venv. Did install_venv.py succeed?"
      exit 1
    fi
    if [ ! -f horizon/bin/test ]; then
      echo "Error: Test script not found at horizon/bin/test. Did buildout succeed?"
      exit 1
    fi
    if [ ! -f horizon/bin/coverage ]; then
      echo "Error: Coverage script not found at horizon/bin/coverage. Did buildout succeed?"
      exit 1
    fi
    if [ ! -f horizon/bin/seleniumrc ]; then
      echo "Error: Selenium script not found at horizon/bin/seleniumrc. Did buildout succeed?"
      exit 1
    fi
  fi
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
    cp -r openstack-dashboard/.dashboard-venv /tmp/.horizon_environment/$JOB_NAME/
    cp -r horizon/bin /tmp/.horizon_environment/$JOB_NAME/
    cp -r horizon/eggs /tmp/.horizon_environment/$JOB_NAME/
    cp -r horizon/parts /tmp/.horizon_environment/$JOB_NAME/
    cp -r horizon/develop-eggs /tmp/.horizon_environment/$JOB_NAME/
    cp -r horizon/horizon.egg-info /tmp/.horizon_environment/$JOB_NAME/
    cp .environment_version /tmp/.horizon_environment/$JOB_NAME/
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

    destroy_buildout

    cp -r /tmp/.horizon_environment/$JOB_NAME/.dashboard-venv openstack-dashboard/
    cp -r /tmp/.horizon_environment/$JOB_NAME/bin horizon/
    cp -r /tmp/.horizon_environment/$JOB_NAME/eggs horizon/
    cp -r /tmp/.horizon_environment/$JOB_NAME/parts horizon/
    cp -r /tmp/.horizon_environment/$JOB_NAME/develop-eggs horizon/
    cp -r /tmp/.horizon_environment/$JOB_NAME/horizon.egg-info horizon/
    cp -r /tmp/.horizon_environment/$JOB_NAME/.environment_version ./

    echo "Environment restored successfully."
  fi
}

function install_venv {
  # Install openstack-dashboard with install_venv.py
  export PIP_DOWNLOAD_CACHE=${PIP_DOWNLOAD_CACHE-/tmp/.pip_download_cache}
  export PIP_USE_MIRRORS=true
  if [ $quiet -eq 1 ]; then
    export PIP_NO_INPUT=true
  fi
  cd openstack-dashboard
  INSTALL_FAILED=0
  python tools/install_venv.py || INSTALL_FAILED=1
  if [ $INSTALL_FAILED -eq 1 ]; then
    echo "Error updating environment with pip, trying without src packages..."
    rm -rf .dashboard-venv/src
    python tools/install_venv.py
  fi
  cd ..
  # Install horizon with buildout
  if [ ! -d /tmp/.buildout_cache ]; then
    mkdir -p /tmp/.buildout_cache
  fi
  cd horizon
  python bootstrap.py
  bin/buildout
  cd ..
  django_wrapper="${django_with_venv}"
  dashboard_wrapper="${dashboard_with_venv}"
  # Make sure it worked and record the environment version
  sanity_check
  chmod -R 754 openstack-dashboard/.dashboard-venv
  echo $environment_version > .environment_version
}

function wait_for_selenium {
  # Selenium can sometimes take several seconds to start.
  STARTED=`grep -irn "Started SocketListener on 0.0.0.0:4444" .selenium_log`
  if [ $? -eq 0 ]; then
    echo "Selenium server started."
    return 0
  fi
  echo -n "."
  sleep 1
  wait_for_selenium
}

function stop_selenium {
  if [ $selenium -eq 1 ]; then
    echo "Stopping Selenium server..."
    SELENIUM_JOB=`ps -elf | grep "seleniumrc" | grep -v grep`
    if [ $? -eq 0 ]; then
        kill `echo "${SELENIUM_JOB}" | awk '{print $4}'`
        echo "Selenium process stopped."
      else
        echo "No selenium process running."
    fi
    rm -f .selenium_log
  fi
}

function run_tests {
  sanity_check

  if [ $selenium -eq 1 ]; then
    stop_selenium
    echo "Starting Selenium server..."
    rm -f .selenium_log
    ${django_wrapper} horizon/bin/seleniumrc > .selenium_log &
    wait_for_selenium
  fi

  echo "Running Horizon application tests"
  ${django_wrapper} coverage erase
  ${django_wrapper} coverage run horizon/bin/test
  # get results of the Horizon tests
  OPENSTACK_RESULT=$?

  echo "Running openstack-dashboard (Django project) tests"
  cd openstack-dashboard
  if [ -f local/local_settings.py ]; then
    cp local/local_settings.py local/local_settings.py.bak
  fi
  cp local/local_settings.py.example local/local_settings.py

  if [ $selenium -eq 1 ]; then
      ${dashboard_wrapper} coverage run dashboard/manage.py test --with-selenium --with-cherrypyliveserver
    else
      ${dashboard_wrapper} coverage run dashboard/manage.py test
  fi
  # get results of the openstack-dashboard tests
  DASHBOARD_RESULT=$?

  if [ -f local/local_settings.py.bak ]; then
    cp local/local_settings.py.bak local/local_settings.py
    rm local/local_settings.py.bak
  fi
  rm local/local_settings.pyc
  cd ..

  if [ $with_coverage -eq 1 ]; then
    echo "Generating coverage reports"
    ${django_wrapper} coverage combine
    ${django_wrapper} coverage xml -i --omit='/usr*,setup.py,*egg*'
    ${django_wrapper} coverage html -i --omit='/usr*,setup.py,*egg*' -d reports
  fi

  stop_selenium

  if [ $(($OPENSTACK_RESULT || $DASHBOARD_RESULT)) -eq 0 ]; then
    echo "Tests completed successfully."
  else
    echo "Tests failed."
  fi
  exit $(($OPENSTACK_RESULT || $DASHBOARD_RESULT))
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

# Build the docs
if [ $just_docs -eq 1 ]; then
    run_sphinx
    exit $?
fi

# PEP8
if [ $just_pep8 -eq 1 ]; then
    run_pep8
    exit $?
fi

# Pylint
if [ $just_pylint -eq 1 ]; then
    run_pylint
    exit $?
fi

# Tab checker
if [ $just_tabs -eq 1 ]; then
    tab_check
    exit $?
fi

# Django development server
if [ $runserver -eq 1 ]; then
    run_server
    exit $?
fi

# Full test suite
run_tests || exit
