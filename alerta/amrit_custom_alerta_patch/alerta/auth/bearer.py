import jwt
from flask_cors import cross_origin

from alerta.auth.utils import create_token, get_customers, not_authorized
from alerta.utils.audit import auth_audit_trail
from alerta.exceptions import ApiError
from alerta.models.permission import Permission
from alerta.models.user import User
from . import auth
import requests
from flask import current_app, jsonify, request

@auth.route('/auth/bearer', methods=['POST'])
@cross_origin(supports_credentials=True)
def bearer():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise ApiError("Missing or invalid Authorization header", 401)

    token = auth_header.replace('Bearer ', '').strip()

    jwks_url = current_app.config.get('VERIFY_JWT_JWKS_ENDPOINT')    

    try:
        if jwks_url:
            current_app.logger.info("Bearer auth in secure mode : using JWKS endpoint to verify JWT token")
            # secure mode : we verify the JWT using the JWKS endpoint :
            jwks_client = jwt.PyJWKClient(jwks_url)
            header = jwt.get_unverified_header(token)
            if 'kid' not in header:
                current_app.logger.warning("No 'kid' in JWT header. Using first available key from JWKS.")
                signing_key = jwks_client.get_signing_keys()[0].key
            else:
                signing_key = jwks_client.get_signing_key(header['kid']).key                

            decoded = jwt.decode(
                token,
                key=signing_key,
                algorithms=["RS256"],
                options={"require": ["sub", "name", "exp"]}
            )
        else :
            # decode JWT token without verify it because it has been done on Amrit Gateway and we trust it
            decoded = jwt.decode(token, options={'verify_signature': False, 'verify_exp': True, 'require' :["sub", "name", "exp","contactId"]})
    except jwt.ExpiredSignatureError:
        raise ApiError("Token expired", 401)
    except jwt.DecodeError:
        raise ApiError("Invalid token", 401)
    
    # Extract info from token :
    email = decoded.get('sub')
    contactId = str(decoded.get('contactId'))
    name = decoded.get('name')
    login = email or contactId
    roles = decoded.get(current_app.config.get('JWT_ROLE_CLAIM', 'roles'), [])
    groups = decoded.get(current_app.config.get('JWT_GROUP_CLAIM', 'groups'), [])

    if not login:
        raise ApiError("Missing login in token. Must contains claims : 'sub' or 'contactId' ", 400)
    
    user = User.find_by_email(email=email) if email else User.find_by_id(id=contactId)

    if not user:
        user = User(id=contactId, name=name, login=login, password='', email=email, roles=current_app.config['USER_ROLES'], text='', email_verified=True)
        user.create()
    else :
        user.update(login=login, email=email, email_verified=True)

    roles += user.roles

    if user.status != 'active':
        raise ApiError(f"User {login} is not active", 403)
    
    if not_authorized('ALLOWED_JWT_ROLES', roles) or not_authorized('ALLOWED_EMAIL_DOMAINS', groups=[user.domain]):
        raise ApiError(f"User {login} is not authorized", 403)
    

    user.update_last_login()
    scopes = Permission.lookup(login, roles=roles)
    customers = get_customers(login, groups=groups + ([user.domain] if user.domain else []))

    auth_audit_trail.send(current_app._get_current_object(), event='bearer-login',
                          message='user login via JWT bearer',
                          user=login, customers=customers, scopes=scopes,
                          roles=roles, groups=groups,
                          resource_id=contactId, type='user', request=request)
    
    token = create_token(user_id=contactId, name=name, login=login,
                                provider='bearer', customers=customers, scopes=scopes,
                                email=email, email_verified=True)
    
    return jsonify(token=token.tokenize())