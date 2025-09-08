import { useState, useEffect, useCallback } from 'react'
import {
  Container,
  Grid2 as Grid,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Skeleton,
} from '@mui/material'
import { Book } from '../types/book'
import { fetchBooks } from '../data/mockBooks'
import BookTile from './BookTile'

interface BooksLandingPageProps {
  onBookClick?: (book: Book) => void
}

const BooksLandingPage = ({ onBookClick }: BooksLandingPageProps) => {
  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  // Function to load more books
  const loadBooks = useCallback(async (page: number, reset: boolean = false) => {
    if (loading) return
    
    setLoading(true)
    setError(null)

    try {
      const response = await fetchBooks(page)
      
      if (reset) {
        setBooks(response.books)
      } else {
        setBooks(prev => [...prev, ...response.books])
      }
      
      setHasMore(response.hasMore)
      setTotalCount(response.totalCount)
      setCurrentPage(page)
    } catch (err) {
      setError('Failed to load books. Please try again.')
      console.error('Error loading books:', err)
    } finally {
      setLoading(false)
    }
  }, [loading])

  // Initial load
  useEffect(() => {
    loadBooks(1, true)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Endless scroll implementation with throttling
  useEffect(() => {
    let timeoutId: NodeJS.Timeout

    const handleScroll = () => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => {
        if (
          window.innerHeight + document.documentElement.scrollTop
          >= document.documentElement.offsetHeight - 1000 // Load more when 1000px from bottom
          && hasMore
          && !loading
        ) {
          loadBooks(currentPage + 1)
        }
      }, 100) // Throttle scroll events to fire at most every 100ms
    }

    window.addEventListener('scroll', handleScroll)
    return () => {
      window.removeEventListener('scroll', handleScroll)
      clearTimeout(timeoutId)
    }
  }, [hasMore, loading, currentPage, loadBooks])

  // Skeleton loader for initial load
  const renderSkeletons = () => (
    <Grid container spacing={3}>
      {Array.from({ length: 12 }, (_, i) => (
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={`skeleton-${i}`}>
          <Box>
            <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />
            <Skeleton variant="text" height={32} sx={{ mt: 1 }} />
            <Skeleton variant="text" height={24} />
            <Skeleton variant="rectangular" height={6} sx={{ mt: 1, borderRadius: 3 }} />
            <Box display="flex" gap={1} mt={1}>
              <Skeleton variant="rounded" width={60} height={24} />
              <Skeleton variant="rounded" width={70} height={24} />
              <Skeleton variant="rounded" width={65} height={24} />
            </Box>
            <Skeleton variant="text" height={20} sx={{ mt: 1 }} />
          </Box>
        </Grid>
      ))}
    </Grid>
  )

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
          Your Library
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          {totalCount > 0 ? `${totalCount} books in your collection` : 'Loading your books...'}
        </Typography>
      </Box>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Books Grid */}
      {books.length === 0 && loading ? (
        renderSkeletons()
      ) : (
        <Grid container spacing={3}>
          {books.map((book) => (
            <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={book.id}>
              <BookTile book={book} onClick={onBookClick} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Loading Indicator for Pagination */}
      {loading && books.length > 0 && (
        <Box display="flex" justifyContent="center" mt={4}>
          <CircularProgress />
        </Box>
      )}

      {/* End of Results Message */}
      {!hasMore && books.length > 0 && (
        <Box textAlign="center" mt={4}>
          <Typography variant="body2" color="text.secondary">
            You've reached the end of your library!
          </Typography>
        </Box>
      )}

      {/* Empty State */}
      {books.length === 0 && !loading && !error && (
        <Box textAlign="center" py={8}>
          <Typography variant="h5" color="text.secondary" gutterBottom>
            No books found
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Start building your library by uploading your first book!
          </Typography>
        </Box>
      )}
    </Container>
  )
}

export default BooksLandingPage