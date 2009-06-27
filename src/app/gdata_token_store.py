## Imported and modified from GDATA code to store in our model,
# and to enable us to get a client for a specified user.

import StringIO
import pickle
import atom.token_store

class TokenStore(atom.token_store.TokenStore):
  """Stores the user's auth tokens in the App Engine datastore.

  Tokens are only written to the datastore if a user is signed in (if 
  users.get_current_user() returns a user object).
  """
  def __init__(self, user):
    self.user = user

  def add_token(self, token):
    """Associates the token with the current user and stores it.
    
    If there is no current user, the token will not be stored.

    Returns:
      False if the token was not stored. 
    """
    tokens = self.load_auth_tokens()
    if not hasattr(token, 'scopes') or not token.scopes:
      return False
    for scope in token.scopes:
      tokens[str(scope)] = token
    key = self.save_auth_tokens(tokens)
    if key:
      return True
    return False

  def find_token(self, url):
    """Searches the current user's collection of token for a token which can
    be used for a request to the url.

    Returns:
      The stored token which belongs to the current user and is valid for the
      desired URL. If there is no current user, or there is no valid user 
      token in the datastore, a atom.http_interface.GenericToken is returned.
    """
    if url is None:
      return None
    if isinstance(url, (str, unicode)):
      url = atom.url.parse_url(url)
    tokens = self.load_auth_tokens()
    if url in tokens:
      token = tokens[url]
      if token.valid_for_scope(url):
        return token
      else:
        del tokens[url]
        self.save_auth_tokens(tokens)
    for scope, token in tokens.iteritems():
      if token.valid_for_scope(url):
        return token
    return atom.http_interface.GenericToken()

  def remove_token(self, token):
    """Removes the token from the current user's collection in the datastore.
    
    Returns:
      False if the token was not removed, this could be because the token was
      not in the datastore, or because there is no current user.
    """
    token_found = False
    scopes_to_delete = []
    tokens = self.load_auth_tokens()
    for scope, stored_token in tokens.iteritems():
      if stored_token == token:
        scopes_to_delete.append(scope)
        token_found = True
    for scope in scopes_to_delete:
      del tokens[scope]
    if token_found:
      self.save_auth_tokens(tokens)
    return token_found

  def remove_all_tokens(self):
    """Removes all of the current user's tokens from the datastore."""
    self.save_auth_tokens({})


  def save_auth_tokens(self, token_dict):
    """Associates the tokens with the current user and writes to the datastore.
  
    If there us no current user, the tokens are not written and this function
    returns None.

    Returns:
      The key of the datastore entity containing the user's tokens, or None if
      there was no current user.
    """
    self.user.pickled_tokens = pickle.dumps(token_dict)
    return self.user.put()
     

  def load_auth_tokens(self):
    """Reads a dictionary of the current user's tokens from the datastore.
  
    If there is no current user (a user is not signed in to the app) or the user
    does not have any tokens, an empty dictionary is returned.
    """
    if self.user.pickled_tokens:
      return pickle.loads(self.user.pickled_tokens)
    return {}

