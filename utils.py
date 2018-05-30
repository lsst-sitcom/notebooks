def whereis(objectname):
    """
    Print a markdown hyperlink to the source code of `objectname`.
    
    Parameters
    ==========
    objectname | object
    The class you are looking for
    
    Comments
    ========
    No error handling whatsoever. Not extensively tested.
    """
    # Locate the module that contains the desired object, and break its name into pieces:
    modulename = objectname.__module__
    pieces = str.split(modulename,'.')
    
    # Form the URL, and a useful markdown representation of it:
    URL = 'https://github.com/'+pieces[0]+'/'+pieces[1]+'_'+pieces[2] \
        + '/blob/master/python/'+pieces[0]+'/'+pieces[1]+'/'+pieces[2]+'/'+pieces[3]+'.py'
    markdown = '['+modulename+']('+URL+')'
    
    from IPython.display import display, Markdown
    display(Markdown(markdown))

    print(markdown)

    return