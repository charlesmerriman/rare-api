# Create Post — Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant PostCreate as PostCreate.js<br/>(React Component)
    participant PostManager as PostManager.js<br/>(API Client)
    participant CORS as CorsMiddleware<br/>(Django)
    participant Auth as TokenAuthentication<br/>(DRF)
    participant View as post_list()<br/>(post_views.py)
    participant ORM as Django ORM
    participant DB as PostgreSQL<br/>(rareapi_post)
    participant FileSystem as File System<br/>(media/images)

    User->>PostCreate: Clicks "Save" button
    PostCreate->>PostCreate: handleSave() — reads form state<br/>(title, category_id, content, imageFile)

    PostCreate->>PostManager: createPost({ title, category_id, content })

    PostManager->>PostManager: authHeader() — reads token from localStorage

    PostManager->>CORS: POST /posts<br/>Authorization: Token <token><br/>Content-Type: application/json

    CORS->>CORS: Validate Origin: localhost:3000

    CORS->>Auth: Forward request

    Auth->>DB: SELECT * FROM authtoken_token WHERE key=<token>
    DB-->>Auth: Token row → RareUser

    Auth->>View: request.user = authenticated RareUser

    View->>View: @permission_classes([IsAuthenticated]) — passes

    View->>ORM: Category.objects.get(pk=category_id)
    ORM->>DB: SELECT * FROM rareapi_category WHERE id=<category_id>
    DB-->>ORM: Category row
    ORM-->>View: category instance

    View->>ORM: Post.objects.create(<br/>  user=request.user,<br/>  category=category,<br/>  title=title,<br/>  content=content,<br/>  publication_date=today,<br/>  approved=user.is_staff<br/>)
    ORM->>DB: INSERT INTO rareapi_post<br/>(user_id, category_id, title, content,<br/>publication_date, approved, image_url)
    DB-->>ORM: New post row (id assigned)
    ORM-->>View: Post instance

    View->>View: PostDetailSerializer(post).data

    View-->>PostManager: 201 Created — { id, title, content, ... }
    PostManager-->>PostCreate: Resolved post object

    alt User selected an image file
        PostCreate->>PostManager: uploadPostImage(post.id, formData)

        PostManager->>CORS: PUT /posts/<id>/image<br/>Authorization: Token <token><br/>Content-Type: multipart/form-data

        CORS->>Auth: Forward request
        Auth->>DB: SELECT authtoken_token (re-validate)
        DB-->>Auth: RareUser

        Auth->>View: upload_post_image(request, pk=post.id)

        View->>View: Validate request.user == post.user

        View->>FileSystem: Write image chunks to<br/>media/post_images/post_<id>_<filename>
        FileSystem-->>View: File saved

        View->>ORM: post.image_url = absolute_url<br/>post.save()
        ORM->>DB: UPDATE rareapi_post SET image_url=<url><br/>WHERE id=<post.id>
        DB-->>ORM: OK
        ORM-->>View: Updated post

        View-->>PostManager: 200 OK — { image_url }
        PostManager-->>PostCreate: Image URL resolved
    end

    PostCreate->>User: navigate("/posts/<id>")
```

## Participants

| Participant | File |
|---|---|
| `PostCreate.js` | [rare-client/src/components/posts/PostCreate.js](../../rare-client/src/components/posts/PostCreate.js) |
| `PostManager.js` | [rare-client/src/managers/PostManager.js](../../rare-client/src/managers/PostManager.js) |
| `post_views.py` | [rare-api/rareapi/views/post_views.py](../rareapi/views/post_views.py) |
| `post_serializers.py` | [rare-api/rareapi/serializers/post_serializers.py](../rareapi/serializers/post_serializers.py) |
| `post.py` (model) | [rare-api/rareapi/models/post.py](../rareapi/models/post.py) |
