#!/bin/bash

set -o errexit

# ---------------UPDATE ME-------------------------------#
# Increment me any time the environment should be rebuilt.
# This includes dependncy changes, directory renames, etc.
# Simple integer secuence: 1, 2, 3...
environment_version=27
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
  echo "  -m, --manage             Run a Django management command."
  echo "  --makemessages           Update all translation files."
  echo "  -p, --pep8               Just run pep8"
  echo "  -t, --tabs               Check for tab characters in files."
  echo "  -y, --pylint             Just run pylint"
  echo "  -q, --quiet              Run non-interactively. (Relatively) quiet."
  echo "                           Implies -V if -N is not set."
  echo "  --only-selenium          Run only the Selenium unit tests"
  echo "  --with-selenium          Run unit tests including Selenium tests"
  echo "  --runserver              Run the Django development server for"
  echo "                           openstack_dashboard in the virtual"
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
root=`pwd`
venv=$root/.venv
with_venv=tools/with_venv.sh
included_dirs="openstack_dashboard horizon"

always_venv=0
backup_env=0
command_wrapper=""
destroy=0
force=0
just_pep8=0
just_pylint=0
just_docs=0
just_tabs=0
never_venv=0
quiet=0
restore_env=0
runserver=0
only_selenium=0
with_selenium=0
testargs=""
with_coverage=0
makemessages=0
manage=0

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
    -m|--manage) manage=1;;
    --makemessages) makemessages=1;;
    --only-selenium) only_selenium=1;;
    --with-selenium) with_selenium=1;;
    --docs) just_docs=1;;
    --runserver) runserver=1;;
    --backup-environment) backup_env=1;;
    --restore-environment) restore_env=1;;
    --destroy-environment) destroy=1;;
    *) testargs="$testargs $1"
  esac
}

function run_management_command {
  ${command_wrapper} python $root/manage.py $testargs
}

function run_server {
  echo "Starting Django development server..."
  ${command_wrapper} python $root/manage.py runserver $testargs
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

function run_pep8 {
  echo "Running pep8 ..."
  ${command_wrapper} pep8 $included_dirs || true
}

function run_sphinx {
    echo "Building sphinx..."
    export DJANGO_SETTINGS_MODULE=openstack_dashboard.settings
    ${command_wrapper} sphinx-build -b html doc/source doc/build/html
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
        command_wrapper="${root}/${with_venv}"
        echo "Environment is up to date."
        return 0
      fi
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

    cp -r /tmp/.horizon_environment/$JOB_NAME/.venv ./ || true
    cp -r /tmp/.horizon_environment/$JOB_NAME/.environment_version ./ || true

    echo "Environment restored successfully."
  fi
}

function install_venv {
  # Install with install_venv.py
  export VIRTUALENV_DISTRIBUTE=true
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
  echo $environment_version > .environment_version
}

function run_tests {
  sanity_check

  if [ $with_selenium -eq 1 ]; then
    export WITH_SELENIUM=1
  elif [ $only_selenium -eq 1 ]; then
    export WITH_SELENIUM=1
    export SKIP_UNITTESTS=1
  fi

  echo "Running Horizon application tests"
  export NOSE_XUNIT_FILE=horizon/nosetests.xml
  if [ "$NOSE_WITH_HTML_OUTPUT" = '1' ]; then
    export NOSE_HTML_OUT_FILE='horizon_nose_results.html'
  fi
  ${command_wrapper} coverage erase
  ${command_wrapper} coverage run -p $root/manage.py test horizon --settings=horizon.tests.testsettings $testargs
  # get results of the Horizon tests
  HORIZON_RESULT=$?

  echo "Running openstack_dashboard tests"
  export NOSE_XUNIT_FILE=openstack_dashboard/nosetests.xml
  if [ "$NOSE_WITH_HTML_OUTPUT" = '1' ]; then
    export NOSE_HTML_OUT_FILE='dashboard_nose_results.html'
  fi
  ${command_wrapper} coverage run -p $root/manage.py test openstack_dashboard --settings=openstack_dashboard.test.settings $testargs
  # get results of the openstack_dashboard tests
  DASHBOARD_RESULT=$?

  if [ $with_coverage -eq 1 ]; then
    echo "Generating coverage reports"
    ${command_wrapper} coverage combine
    ${command_wrapper} coverage xml -i --omit='/usr*,setup.py,*egg*,.venv/*'
    ${command_wrapper} coverage html -i --omit='/usr*,setup.py,*egg*,.venv/*' -d reports
  fi
  # Remove the leftover coverage files from the -p flag earlier.
  rm -f .coverage.*

  if [ $(($HORIZON_RESULT || $DASHBOARD_RESULT)) -eq 0 ]; then
    echo "Tests completed successfully."
  else
    echo "Tests failed."
  fi
  exit $(($HORIZON_RESULT || $DASHBOARD_RESULT))
}

function run_makemessages {
  cd horizon
  ${command_wrapper} $root/manage.py makemessages --all --no-obsolete
  HORIZON_PY_RESULT=$?
  ${command_wrapper} $root/manage.py makemessages -d djangojs --all --no-obsolete
  HORIZON_JS_RESULT=$?
  cd ../openstack_dashboard
  ${command_wrapper} $root/manage.py makemessages --all --no-obsolete
  DASHBOARD_RESULT=$?
  cd ..
  exit $(($HORIZON_PY_RESULT || $HORIZON_JS_RESULT || $DASHBOARD_RESULT))
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
