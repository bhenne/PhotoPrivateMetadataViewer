Here you get some help on building pyexiv2 with Region tagging support.

1) Build and install exiv2/libexiv2 0.22 with my patch or 0.23+

2) Building pyexiv2

  * Ubuntu 12.04 (installed exiv2 v0.23 before)
     It's just this:

     sudo apt-get install bzr scons libboost-python-dev
     bzr branch lp:pyexiv2	
     cd pyexiv2
     scons
     sudo scons install

  * OS X Lion (installed exiv2 v0.23 using brewi before)

    brew search pyexiv2
     No formula found for "pyexiv2". Searching open pull requests...
     https://github.com/mxcl/homebrew/pull/11764
    
    curl https://raw.github.com/camillol/homebrew/79f851199ed4bdf98e8d887ac2abe92b210d9988/Library/Formula/pyexiv2.rb >`brew --prefix`/Library/Formula/pyexiv2.rb
    vim `brew --prefix`/Library/Formula/pyexiv2.rb
    
     -  url 'http://launchpad.net/pyexiv2/0.3.x/0.3.2/+download/pyexiv2-0.3.2.tar.bz2'
     -  sha1 'ad20ea6925571d58637830569076aba327ff56d9'
     +  head 'lp:pyexiv2', :using => :bzr
    
    brew install bazaar
    brew install --HEAD pyexiv2

    #For non-homebrew Python, you need to amend your PYTHONPATH like so:
    #  export PYTHONPATH=/usr/local/lib/python2.7/site-packages:$PYTHONPATH


