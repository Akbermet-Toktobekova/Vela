"""Trusted asymmetric Supabase JWT identity. Never obtain trust from a token."""
from dataclasses import dataclass
import os
import secrets
from threading import RLock
import time
from urllib.parse import urlsplit

import httpx
import jwt
from fastapi import HTTPException


def unauthorized():
    return HTTPException(401, 'Your session is invalid or expired. Sign in again.', headers={'WWW-Authenticate': 'Bearer'})


def unavailable():
    return HTTPException(503, 'Sign-in verification is temporarily unavailable. Try again.')


@dataclass(frozen=True)
class SupabaseJWTConfig:
    project_url: str
    issuer: str
    audience: str
    jwks_url: str
    algorithms: tuple[str, ...]

    def __post_init__(self):
        origin = urlsplit(self.project_url)
        if (origin.scheme != 'https' or not origin.hostname or origin.username or origin.password
                or origin.path or origin.query or origin.fragment or '*' in self.project_url):
            raise RuntimeError('Configure the trusted HTTPS Supabase project origin.')
        origin.port
        if self.issuer != self.project_url + '/auth/v1' or self.jwks_url != self.issuer + '/.well-known/jwks.json':
            raise RuntimeError('JWT issuer and JWKS URL must match the configured Supabase project.')
        if not isinstance(self.audience, str) or not self.audience.strip():
            raise RuntimeError('Configure the expected JWT audience.')
        if not self.algorithms or len(set(self.algorithms)) != len(self.algorithms) or not set(self.algorithms) <= {'RS256', 'ES256'}:
            raise RuntimeError('Configure explicit supported asymmetric JWT algorithms (RS256/ES256).')

    @classmethod
    def from_env(cls):
        return cls(os.getenv('SUPABASE_URL', ''), os.getenv('SUPABASE_JWT_ISSUER', ''),
                   os.getenv('SUPABASE_JWT_AUDIENCE', ''), os.getenv('SUPABASE_JWKS_URL', ''),
                   tuple(a.strip() for a in os.getenv('SUPABASE_JWT_ALGORITHMS', '').split(',') if a.strip()))


class SupabaseJWTVerifier:
    def __init__(self, config, transport=None, clock=None, monotonic=None):
        self.config = config
        self.transport = transport
        self.clock = clock or time.time
        self.monotonic = monotonic or time.monotonic
        self._keys = {}
        self._expires = 0
        self._last_fetch = None
        self._lock = RLock()

    def _refresh(self):
        try:
            with httpx.Client(transport=self.transport, timeout=5, follow_redirects=False, trust_env=False) as client:
                with client.stream('GET', self.config.jwks_url) as response:
                    response.raise_for_status()
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > 65536:
                            raise ValueError('JWKS too large')
            import json
            document = json.loads(content)
            keys = document['keys']
            if not isinstance(keys, list) or not keys or len(keys) > 32:
                raise ValueError('Invalid JWKS')
            parsed, seen = {}, set()
            for key in keys:
                if not isinstance(key, dict):
                    raise ValueError('Invalid JWK')
                kid = key.get('kid')
                if not isinstance(kid, str) or not kid or len(kid) > 200 or kid in seen:
                    raise ValueError('Invalid key identity')
                seen.add(kid)
                if key.get('use', 'sig') != 'sig' or key.get('kty') not in ('RSA', 'EC'):
                    continue
                if key.get('key_ops', ['verify']) != ['verify']:
                    continue
                algorithm = key.get('alg')
                candidates = (algorithm,) if algorithm else self.config.algorithms
                for candidate in candidates:
                    if candidate not in self.config.algorithms:
                        continue
                    if (candidate == 'RS256' and key['kty'] != 'RSA') or (candidate == 'ES256' and (key['kty'] != 'EC' or key.get('crv') != 'P-256')):
                        continue
                    parsed[(kid, candidate)] = jwt.PyJWK.from_dict(key, algorithm=candidate).key
            if not parsed:
                raise ValueError('No supported verification keys')
            self._keys = parsed
            self._expires = self.monotonic() + 600
            self._last_fetch = self.monotonic()
        except (httpx.HTTPError, ValueError, KeyError, TypeError, jwt.PyJWTError):
            self._last_fetch = self.monotonic()
            raise unavailable() from None

    def owner(self, authorization):
        if not isinstance(authorization, str):
            raise unauthorized()
        parts = authorization.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer' or not parts[1] or len(parts[1]) > 16384:
            raise unauthorized()
        token = parts[1]
        try:
            header = jwt.get_unverified_header(token)
            algorithm, kid = header.get('alg'), header.get('kid')
            if (algorithm not in self.config.algorithms or not isinstance(kid, str) or not kid or len(kid) > 200
                    or any(field in header for field in ('jku', 'x5u', 'jwk', 'crit'))):
                raise unauthorized()
            with self._lock:
                now = self.monotonic()
                if not self._keys or now >= self._expires:
                    # Bound repeated provider failures as well as unknown-kid traffic.
                    if self._last_fetch is not None and now-self._last_fetch < 1:
                        raise unavailable()
                    self._refresh()
                key = self._keys.get((kid, algorithm))
                if key is None:
                    # Refresh once for rotation; a one-second cooldown bounds random-kid floods.
                    if self._last_fetch is None or now-self._last_fetch >= 1:
                        self._refresh()
                    key = self._keys.get((kid, algorithm))
                if key is None:
                    raise unauthorized()
            claims = jwt.decode(token, key, algorithms=list(self.config.algorithms), issuer=self.config.issuer,
                                audience=self.config.audience, options={'require': ['exp', 'iss', 'aud', 'sub'],
                                'verify_exp': False, 'verify_iat': False, 'verify_nbf': False})
            now = self.clock()
            if type(claims['exp']) is not int or claims['exp'] <= now:
                raise unauthorized()
            for field in ('iat', 'nbf'):
                if field in claims and (type(claims[field]) is not int or claims[field] > now):
                    raise unauthorized()
            subject = claims['sub']
            if not isinstance(subject, str) or not subject.strip() or subject != subject.strip() or len(subject) > 128 or subject == 'local-demo':
                raise unauthorized()
            return subject
        except (jwt.PyJWTError, TypeError, ValueError, KeyError):
            raise unauthorized() from None


def local_owner(authorization, token):
    if not authorization or not secrets.compare_digest(authorization, f'Bearer {token}'):
        raise HTTPException(401, 'Connect this device using your local token.')
    return 'local-demo'
