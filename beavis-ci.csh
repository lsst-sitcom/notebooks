#! /usr/bin/env tcsh
#=======================================================================
#+
# NAME:
#   beavis-ci.csh
#
# PURPOSE:
#   Enable occasional integration and testing. Like travis-ci but dumber.
#
# COMMENTS:
#   This script is utterly unuseable since the jupyterlab instance 
#   does not provide the tcsh shell. But, it could be translated to bash
#   for the win.
#
# INPUTS:
#
# OPTIONAL INPUTS:
#   -h --help     Print this header
#   -u --username GITHUB_USERNAME, defaults to the environment variable
#   -k --key      GITHUB_API_KEY, defaults to the environment variable
#   -n --no-push  Only run the notebooks, don't deploy the html
#
# OUTPUTS:
#
# EXAMPLES:
#
#   ./beavis-ci.csh
#
#-
# ======================================================================

set help = 0
set just_testing = 1

while ( $#argv > 0 )
    switch ($argv[1])
    case -h:
        shift argv
        set help = 1
        breaksw
    case --{help}:
        shift argv
        set help = 1
        breaksw
    case -n:
        shift argv
        set just_testing = 0
        breaksw
    case --{no-push}:
        shift argv
        set just_testing = 0
        breaksw
    case -u:
        shift argv
        set GITHUB_USERNAME = $argv[1]
        shift argv
        breaksw
    case --{username}:
        shift argv
        set GITHUB_USERNAME = $argv[1]
        shift argv
        breaksw   
    case -k:
        shift argv
        set GITHUB_API_KEY = $argv[1]
        shift argv
        breaksw
    case --{key}:
        shift argv
        set GITHUB_API_KEY = $argv[1]
        shift argv
        breaksw   
    endsw
end

if ($help) then
  more $0
  goto FINISH
endif

# Check out a fresh clone in a temporary hidden folder, over-writing 
# any previous edition:
\rm -rf .beavis ; mkdir .beavis ; cd .beavis
git clone git@github.com:lsst-com/notebooks.git
cd notebooks

echo "Making static HTML pages from the available notebooks:"
set htmlfiles = ()
foreach notebook ( *.ipynb )
    set logfile = $notebook:r.log
    jupyter nbconvert --ExecutePreprocessor.kernel_name=LSST \
                      --ExecutePreprocessor.timeout=600 --to HTML \
                      --execute $notebook >& $logfile
    set htmlfile = $notebook:r.html
    if ( -e $htmlfile) then
        set htmlfiles = ( $htmlfiles $htmlfile )
        du -h $notebook:r.html
    else
        echo "WARNING: $htmlfile was not created, read the log in $logfile for details."
    endif
end

if just_testing goto CLEANUP:
# Otherwise:

echo "Attempting to push the HTML to GitHub in an orphan html branch..."
# Check for GitHub credentials and then push the pages up:
if ( $?GITHUB_USERNAME && $?GITHUB_API_KEY ) then

    set branch = html
    echo "...with key $GITHUB_API_KEY and username $GITHUB_USERNAME"

    echo -n "If this looks OK, hit any key to continue..."
    set goforit = $<

    git branch -D $branch >& /dev/null
    git checkout --orphan $branch
    git rm -rf .
    git add -f $htmlfiles
    git commit -m "pushed HTML"
    git push -q -f \
        https://${GITHUB_USERNAME}:${GITHUB_API_KEY}@github.com/lsst-com/notebooks $branch
    echo "Done!"
    git checkout $branch

    echo ""
    echo "Please read the above output very carefully to see that things are OK. To check we've come back to the dev branch correctly, here's a git status:"
    echo ""

    git status

else
    echo "...No GITHUB_API_KEY and/or GITHUB_USERNAME set, giving up."
endif


CLEANUP:
cd ../../
# \rm -rf .beavis
# Uncomment the above when script works!

# ======================================================================
FINISH:
# ======================================================================