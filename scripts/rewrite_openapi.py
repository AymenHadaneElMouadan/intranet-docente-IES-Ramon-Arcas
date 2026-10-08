# Transform OpenAPI to teacher conventions. Run from repo root:
#   python scripts/rewrite_openapi.py
from pathlib import Path

path = Path("openapi/openapi.yaml")
text = path.read_text(encoding="utf-8")

def must_replace(old: str, new: str, label: str) -> str:
    global text
    if old not in text:
        raise SystemExit(f"Block not found: {label}")
    text = text.replace(old, new)
    print("OK", label)


must_replace(
    """      description: |
        Recibe credenciales OAuth de Google y emite access + refresh token.
        **PENDIENTE DE DECISIÓN:** forma exacta del credential y restricción de dominio.
""",
    """      description: |
        Recibe `id_token` de Google Identity Services.
        Emite access JWT en el body y refresh en cookie HttpOnly `refresh_token`.
        Sin restriccion de dominio; usuarios nuevos quedan en estado `pendiente`.
""",
    "auth-google-desc",
)

must_replace(
    """        '200':
          description: Tokens emitidos
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenPairResponse'
""",
    """        '200':
          description: Access token emitido (refresh en Set-Cookie)
          headers:
            Set-Cookie:
              description: Cookie HttpOnly refresh_token
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AccessTokenResponse'
""",
    "auth-google-200",
)

must_replace(
    """  /api/v1/auth/refresh:
    post:
      tags: [Auth]
      summary: Renovar access token
      description: |
        Usa el refresh token (no el access token).
        **PENDIENTE DE DECISIÓN:** body JSON vs cookie HttpOnly.
      operationId: authRefresh
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RefreshRequest'
      responses:
        '200':
          description: Nuevo access token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenPairResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
""",
    """  /api/v1/auth/refresh:
    post:
      tags: [Auth]
      summary: Renovar access token
      description: |
        Lee la cookie HttpOnly `refresh_token` (no usa Bearer).
        Valida el token opaco en Redis y emite un nuevo access JWT.
      operationId: authRefresh
      security: []
      parameters:
        - name: refresh_token
          in: cookie
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Nuevo access token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AccessTokenResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
""",
    "auth-refresh",
)

must_replace(
    """  /api/v1/auth/logout:
    post:
      tags: [Auth]
      summary: Cerrar sesión
      description: Invalida el refresh token en Redis.
      operationId: authLogout
      security:
        - BearerAuth: []
      requestBody:
        required: false
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LogoutRequest'
      responses:
        '200':
          description: Sesión invalidada
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MessageResponse'
              example:
                code: 200
                msg: La operacion se ha realizado correctamente
        '401':
          $ref: '#/components/responses/Unauthorized'
""",
    """  /api/v1/auth/logout:
    post:
      tags: [Auth]
      summary: Cerrar sesión
      description: Invalida el refresh en Redis y borra la cookie.
      operationId: authLogout
      security:
        - BearerAuth: []
      responses:
        '200':
          description: Sesión invalidada
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DetailMessage'
              example:
                detail: Sesion cerrada
        '401':
          $ref: '#/components/responses/Unauthorized'
""",
    "auth-logout",
)

must_replace(
    """  /api/v1/usuarios:
    get:
      tags: [Usuarios]
      summary: Listado del claustro
      operationId: listUsuarios
      security:
        - BearerAuth: []
      parameters:
        - name: departamento
          in: query
          required: false
          schema:
            type: string
          description: Filtro por departamento
      responses:
        '200':
          description: Lista de usuarios
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Usuario'
              example:
                - id: "64f1a2b3c4d5e6f7a8b9c0d1"
                  name: Jose
                  departamento: Informatica
                  roles: [docente]
                  estado_alta: activo
                - id: "64f1a2b3c4d5e6f7a8b9c0d2"
                  name: Juan
                  departamento: Matematicas
                  roles: [docente, tutor]
                  estado_alta: activo
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'

  /api/v1/usuarios/me:
""",
    """  /api/v1/usuarios:
    get:
      tags: [Usuarios]
      summary: Listado del claustro
      description: Requiere rol admin. Admite filtro y paginacion.
      operationId: listUsuarios
      security:
        - BearerAuth: []
      parameters:
        - name: departamento
          in: query
          required: false
          schema:
            type: string
          description: Filtra por departamento
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/Limit'
      responses:
        '200':
          description: Pagina de usuarios
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UsuarioPaginated'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
    post:
      tags: [Usuarios]
      summary: Alta manual de usuario
      description: El servidor asigna el id. Cabecera Location apunta al GET por id.
      operationId: createUsuario
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UsuarioCreate'
            example:
              name: Pepa
              email: pepa@example.com
              departamento: FOL
              roles: [docente]
      responses:
        '201':
          description: Usuario creado
          headers:
            Location:
              description: URL del recurso creado
              schema:
                type: string
                example: /api/v1/usuarios/64f1a2b3c4d5e6f7a8b9c0d3
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Usuario'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '409':
          $ref: '#/components/responses/Conflict'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'

  /api/v1/usuarios/me:
""",
    "usuarios-list-post",
)

must_replace(
    """  /api/v1/usuarios/{id}:
    patch:
      tags: [Usuarios]
      summary: Modificación parcial de usuario
      description: Ejemplo de uso — aprobar alta pendiente.
      operationId: patchUsuario
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/UsuarioId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UsuarioPatch'
            example:
              estado_alta: activo
              departamento: Informatica
      responses:
        '200':
          description: Usuario actualizado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MessageWithData'
              example:
                code: 200
                msg: La operacion se ha realizado correctamente
                data:
                  id: "64f1a2b3c4d5e6f7a8b9c0d1"
                  estado_alta: activo
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
""",
    """  /api/v1/usuarios/{id}:
    get:
      tags: [Usuarios]
      summary: Obtener un usuario
      operationId: getUsuario
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/UsuarioId'
      responses:
        '200':
          description: Usuario
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Usuario'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
    patch:
      tags: [Usuarios]
      summary: Modificacion parcial de usuario
      description: Ejemplo de uso — aprobar alta pendiente (`estado: activo`).
      operationId: patchUsuario
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/UsuarioId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UsuarioPatch'
            example:
              estado: activo
              departamento: Informatica
      responses:
        '200':
          description: Usuario actualizado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Usuario'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
""",
    "usuarios-get-patch",
)

# Anuncios create response
must_replace(
    """        '201':
          description: Anuncio creado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MessageWithData'
              example:
                code: 201
                msg: La operacion se ha realizado correctamente
""",
    """        '201':
          description: Anuncio creado
          headers:
            Location:
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Anuncio'
""",
    "anuncios-201",
)

text = text.replace(
    "$ref: '#/components/schemas/MessageWithData'",
    "$ref: '#/components/schemas/ResourceAck'",
)
text = text.replace(
    "$ref: '#/components/schemas/MessageResponse'",
    "$ref: '#/components/schemas/DetailMessage'",
)
text = text.replace(
    "$ref: '#/components/schemas/ErrorResponse'",
    "$ref: '#/components/schemas/ErrorDetail'",
)
text = text.replace("estado_alta", "estado")

must_replace(
    """    ResourceId:
      name: id
      in: path
      required: true
      schema:
        type: string
      description: Identificador del recurso (codificado en la URL)

  responses:
""",
    """    ResourceId:
      name: id
      in: path
      required: true
      schema:
        type: string
      description: Identificador del recurso (codificado en la URL)
    Page:
      name: page
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        default: 1
    Limit:
      name: limit
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        maximum: 50
        default: 10

  responses:
""",
    "pagination-params",
)

must_replace(
    """  responses:
    BadRequest:
      description: Petición incorrecta
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            code: 400
            msg: Peticion incorrecta
    Unauthorized:
      description: No autenticado
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            code: 401
            msg: No autenticado
    Forbidden:
      description: Sin permisos
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            code: 403
            msg: No autorizado
    NotFound:
      description: Recurso no encontrado
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            code: 404
            msg: Recurso no encontrado
    UnprocessableEntity:
      description: Validación fallida o transición inválida
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            code: 422
            msg: Datos no validos
            details:
              - field: estado
                issue: Transicion no permitida
""",
    """  responses:
    BadRequest:
      description: Peticion incorrecta
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            detail: Peticion incorrecta
    Unauthorized:
      description: No autenticado
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            detail: No autenticado
    Forbidden:
      description: Sin permisos
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            detail: Se requiere uno de estos roles: admin
    NotFound:
      description: Recurso no encontrado
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            detail: Recurso no encontrado
    Conflict:
      description: Conflicto (duplicado, solapamiento o transicion no valida)
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
          example:
            detail: El recurso ya existe
    UnprocessableEntity:
      description: Validacion fallida
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorDetail'
""",
    "error-responses",
)

# Replace schemas from MessageResponse through Horario
start = text.index("    MessageResponse:")
end = text.index("    Anuncio:")
new_schemas = """    ErrorDetail:
      type: object
      required: [detail]
      properties:
        detail:
          description: Mensaje o lista de errores de validacion (estilo FastAPI)

    DetailMessage:
      type: object
      required: [detail]
      properties:
        detail:
          type: string

    ResourceAck:
      type: object
      description: Respuesta generica de accion de negocio (modulos pendientes)
      additionalProperties: true

    GoogleAuthRequest:
      type: object
      required: [id_token]
      properties:
        id_token:
          type: string
          description: ID token JWT emitido por Google Identity Services

    AccessTokenResponse:
      type: object
      required: [access_token, token_type, expires_in]
      properties:
        access_token:
          type: string
        token_type:
          type: string
          example: bearer
        expires_in:
          type: integer
          description: Segundos de validez del access token

    UsuarioEstado:
      type: string
      enum: [pendiente, activo, inactivo]

    Usuario:
      type: object
      required: [id, name, email, departamento, roles, estado]
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
          format: email
        departamento:
          type: string
        roles:
          type: array
          items:
            $ref: '#/components/schemas/Role'
        estado:
          $ref: '#/components/schemas/UsuarioEstado'

    UsuarioPaginated:
      type: object
      required: [items, page, limit, total]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Usuario'
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer

    UsuarioCreate:
      type: object
      required: [name, email, departamento]
      properties:
        name:
          type: string
        email:
          type: string
          format: email
        departamento:
          type: string
        roles:
          type: array
          items:
            $ref: '#/components/schemas/Role'
          default: [docente]
        estado:
          $ref: '#/components/schemas/UsuarioEstado'
          default: activo

    UsuarioMe:
      allOf:
        - $ref: '#/components/schemas/Usuario'
        - type: object
          properties:
            permisos:
              type: array
              items:
                type: string

    UsuarioPatch:
      type: object
      properties:
        name:
          type: string
        departamento:
          type: string
        roles:
          type: array
          items:
            $ref: '#/components/schemas/Role'
        estado:
          $ref: '#/components/schemas/UsuarioEstado'

    BloqueHorario:
      type: object
      required: [inicio, fin, tipo]
      properties:
        inicio:
          type: string
          example: "08:00"
        fin:
          type: string
          example: "09:00"
        tipo:
          type: string
          enum: [clase, guardia, reduccion]
        asignatura:
          type: string
        grupo:
          type: string
        aula:
          type: string

    Horario:
      type: object
      required: [usuario_id, dias]
      properties:
        usuario_id:
          type: string
        dias:
          type: object
          additionalProperties:
            type: array
            items:
              $ref: '#/components/schemas/BloqueHorario'
          description: Mapa dia -> bloques (lunes, martes, ...)

"""
text = text[:start] + new_schemas + text[end:]
print("OK schemas")

text = text.replace(
    "        **PENDIENTE DE DECISIÓN:** detalle del algoritmo.\n",
    "        Detalle del algoritmo: pendiente de implementacion (Fase 3).\n",
)

path.write_text(text, encoding="utf-8")
print("Written", path)
print("leftovers MessageWithData", text.count("MessageWithData"))
print("leftovers MessageResponse", text.count("MessageResponse"))
print("leftovers ErrorResponse", text.count("ErrorResponse"))
print("leftovers TokenPair", text.count("TokenPairResponse"))
print("leftovers estado_alta", text.count("estado_alta"))
