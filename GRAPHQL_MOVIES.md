# GraphQL Movies Endpoint

This document describes the GraphQL implementation for fetching movies, which provides the same functionality as the REST endpoint `/api/movies/` but in GraphQL format.

## Endpoint

- **URL**: `/graphql`
- **Method**: POST
- **Content-Type**: application/json

## Schema

### Query: movies

Fetches a paginated list of movies with the same filtering and sorting capabilities as the REST endpoint.

#### Parameters

| Parameter   | Type      | Default  | Description                    |
| ----------- | --------- | -------- | ------------------------------ |
| `page`      | Int       | 1        | Page number for pagination     |
| `size`      | Int       | 30       | Number of items per page       |
| `sortBy`    | SortBy    | RATED_AT | Field to sort by               |
| `sortOrder` | SortOrder | DESC     | Sort direction                 |
| `lang`      | Language  | UK       | Language for localized content |

#### Enums

**SortBy**

- `RATING` - Sort by average rating
- `RATINGS_COUNT` - Sort by number of ratings
- `RATED_AT` - Sort by when last rated
- `RELEASE_DATE` - Sort by release date
- `RANDOM` - Random order
- `ID` - Sort by movie ID

**SortOrder**

- `ASC` - Ascending order
- `DESC` - Descending order

**Language**

- `UK` - Ukrainian
- `EN` - English

#### Response Type: MoviesResponse

```graphql
type MoviesResponse {
  items: [MoviePreview!]!
  total: Int!
  page: Int!
  size: Int!
  pages: Int!
}

type MoviePreview {
  key: String!
  title: String!
  poster: String
  releaseDate: DateTime!
  duration: String!
  mainGenre: String!
  rating: Float!
}
```

## Example Queries

### Basic Query

```graphql
query GetMovies {
  movies(page: 1, size: 10) {
    items {
      key
      title
      poster
      releaseDate
      duration
      mainGenre
      rating
    }
    total
    page
    size
    pages
  }
}
```

### Query with Parameters

```graphql
query GetMoviesSorted {
  movies(page: 1, size: 5, sortBy: RELEASE_DATE, sortOrder: ASC, lang: EN) {
    items {
      key
      title
      duration
      mainGenre
    }
    total
    pages
  }
}
```

### Query with User Context

To include user-specific data (like personal ratings), include the user UUID in the request headers:

```bash
curl -X POST http://localhost:8000/graphql \
  -H 'Content-Type: application/json' \
  -H 'user-uuid: your-user-uuid-here' \
  -d '{"query": "query { movies(page: 1, size: 5) { items { key title rating } } }"}'
```

## Implementation Details

### Context Setup

The GraphQL resolver receives context with:

- `db`: Database session
- `current_user`: Current user (if authenticated via user-uuid header)
- `request`: FastAPI request object

### Reused Logic

The GraphQL implementation reuses the existing REST endpoint logic:

- `build_movie_query()` for query building
- `get_main_genres_for_movies()` for genre mapping
- Same pagination and sorting logic
- Same user authentication and permission handling

### Authentication

User authentication works via:

1. `user-uuid` header
2. `user_uuid` query parameter

Example:

```
GET /graphql?user_uuid=your-uuid-here
```

## Testing

### Using GraphQL Playground

1. Start the FastAPI server
2. Navigate to `http://localhost:8000/graphql`
3. Use the interactive GraphQL Playground

### Using curl

```bash
curl -X POST http://localhost:8000/graphql \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "query { movies(page: 1, size: 5) { items { key title } total } }"
  }'
```

### Using the Test Script

Run the provided integration test:

```bash
python test_graphql_integration.py
```

## Comparison with REST Endpoint

| Feature          | REST `/api/movies/`     | GraphQL `movies`           |
| ---------------- | ----------------------- | -------------------------- |
| Pagination       | ✅ Query params         | ✅ Arguments               |
| Sorting          | ✅ Query params         | ✅ Arguments               |
| Language         | ✅ Query params         | ✅ Arguments               |
| User context     | ✅ Dependency injection | ✅ Context                 |
| Field selection  | ❌ Fixed response       | ✅ Flexible selection      |
| Multiple queries | ❌ Single endpoint      | ✅ Multiple in one request |

## Future Enhancements

1. **Filtering**: Add genre, actor, director filtering
2. **Search**: Add search capabilities
3. **Mutations**: Add create/update/delete operations
4. **Subscriptions**: Add real-time updates
5. **Nested queries**: Add related data fetching (actors, directors, etc.)
