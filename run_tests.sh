#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Openstack Dashboard's test suite(s)"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv.  Install automatically"
  echo "                           if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv.  Run tests in local"
  echo "                           environment"
  echo "  -f, --force              Force a clean re-build of the virtual"
  echo "                           environment. Useful when dependencies have"
  echo "                           been added."
  echo "  -p, --pep8               Just run pep8"
  echo "  -y, --pylint             Just run pylint"
  echo "  --docs                   Just build the documentation"
  echo "  -h, --help               Print this usage message"
  echo ""
  echo "Note: with no options specified, the script will try to run the tests in"
  echo "  a virtual environment,  If no virtualenv is found, the script will ask"
  echo "  if you would like to create one.  If you prefer to run tests NOT in a"
  echo "  virtual environment, simply pass the -N option."
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) let always_venv=1; let never_venv=0;;
    -N|--no-virtual-env) let always_venv=0; let never_venv=1;;
    -p|--pep8) let just_pep8=1;;
    -y|--pylint) let just_pylint=1;;
    -f|--force) let force=1;;
    --docs) let just_docs=1;;
    *) testargs="$testargs $1"
  esac
}

function run_pylint {
  echo "Running pylint ..."
  PYLINT_INCLUDE="openstack-dashboard/dashboard django-openstack/django_openstack"
  ${django_wrapper} pylint --rcfile=.pylintrc -f parseable $PYLINT_INCLUDE > pylint.txt
  CODE=$?
  grep Global -A2 pylint.txt
  if [ $CODE -lt 32 ]
  then
      exit 0
  else
      exit $CODE
  fi
}

function run_pep8 {
  echo "Running pep8 ..."
  PEP8_EXCLUDE=vcsversion.py
  PEP8_OPTIONS="--exclude=$PEP8_EXCLUDE --repeat"
  PEP8_INCLUDE="openstack-dashboard/dashboard django-openstack/django_openstack"
  echo "${django_wrapper} pep8 $PEP8_OPTIONS $PEP8_INCLUDE > pep8.txt"
  #${django_wrapper} pep8 $PEP8_OPTIONS $PEP8_INCLUDE > pep8.txt
  #perl string strips out the [ and ] characters
  ${django_wrapper} pep8 $PEP8_OPTIONS $PEP8_INCLUDE | perl -ple 's/: ([WE]\d+)/: [$1]/' > pep8.txt
}

function run_sphinx {
    echo "Building sphinx..."
    echo "${django_wrapper} export DJANGO_SETTINGS_MODULE=local.local_settings"
    ${django_wrapper} export DJANGO_SETTINGS_MODULE=local.local_settings
    echo "${django_wrapper} python doc/generate_autodoc_index.py"
    ${django_wrapper} python doc/generate_autodoc_index.py
    echo "${django_wrapper} sphinx-build -b html doc/source build/sphinx/html"
    ${django_wrapper} sphinx-build -b html doc/source build/sphinx/html
}


# DEFAULTS FOR RUN_TESTS.SH
#
venv=openstack-dashboard/.dashboard-venv
django_with_venv=openstack-dashboard/tools/with_venv.sh
dashboard_with_venv=tools/with_venv.sh
always_venv=0
never_venv=0
force=0
testargs=""
django_wrapper=""
dashboard_wrapper=""
just_pep8=0
just_pylint=0
just_docs=0

# PROCESS ARGUMENTS, OVERRIDE DEFAULTS
for arg in "$@"; do
    process_option $arg
done

if [ $never_venv -eq 0 ]
then
  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    echo "Cleaning virtualenv..."
    rm -rf ${venv}
  fi
  if [ -e ${venv} ]; then
    django_wrapper="${django_with_venv}"
    dashboard_wrapper="${dashboard_with_venv}"
  else
    if [ $always_venv -eq 1 ]; then
      # Automatically install the virtualenv
      cd openstack-dashboard
      python tools/install_venv.py
      cd ..
      django_wrapper="${django_with_venv}"
      dashboard_wrapper="${dashboard_with_venv}"
    else
      echo -e "No virtual environment found...create one? (Y/n) \c"
      read use_ve
      if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
        # Install the virtualenv and run the test suite in it
        cd openstack-dashboard
        python tools/install_venv.py
        cd ..
        django_wrapper="${django_with_venv}"
        dashboard_wrapper="${dashboard_with_venv}"
      fi
    fi
  fi
fi

function run_tests {
  echo "Running django-openstack (core django) tests"
  ${django_wrapper} coverage erase
  cd django-openstack
  python bootstrap.py
  bin/buildout
  cd ..
  ${django_wrapper} coverage run django-openstack/bin/test
  # get results of the django-openstack tests
  OPENSTACK_RESULT=$?

  echo "Running openstack-dashboard (django website) tests"
  cd openstack-dashboard
  cp local/local_settings.py.example local/local_settings.py
  ${dashboard_wrapper} coverage run dashboard/manage.py test
  # get results of the openstack-dashboard tests
  DASHBOARD_RESULT=$?
  cd ..

  echo "Generating coverage reports"
  ${django_wrapper} coverage combine
  ${django_wrapper} coverage xml --omit='/usr*,setup.py,*egg*'
  ${django_wrapper} coverage html --omit='/usr*,setup.py,*egg*' -d reports
  exit $(($OPENSTACK_RESULT || $DASHBOARD_RESULT))
}

if [ $just_docs -eq 1 ]; then
    run_sphinx
    exit $?
fi

if [ $just_pep8 -eq 1 ]; then
    run_pep8
    exit $?
fi

if [ $just_pylint -eq 1 ]; then
    run_pylint
    exit $?
fi

run_tests || exit
