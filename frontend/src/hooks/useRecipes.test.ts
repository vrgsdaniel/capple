import { act, renderHook, waitFor } from '@testing-library/react'
import api from '@/lib/api'
import { useRecipes } from '@/hooks/useRecipes'

jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}))

const mockedApi = api as unknown as { get: jest.Mock }

function makeListItem(overrides = {}) {
  return {
    id: 'r1',
    name: 'Pasta',
    recipe_type: 'dinner',
    labels: ['quick'],
    prep_time_minutes: 10,
    cook_time_minutes: 20,
    rating: 4,
    image_uri: 'https://example.com/pasta.jpg',
    ...overrides,
  }
}

function makeDetail(overrides = {}) {
  return {
    ...makeListItem(),
    ingredients: [{ item: 'pasta', amount: '200g' }],
    instructions: 'Boil water\nCook pasta',
    source_name: 'Bon Appétit',
    source_url: 'https://bonappetit.com/recipe/pasta',
    servings: 4,
    image_uri: 'https://example.com/pasta-hd.jpg',
    ...overrides,
  }
}

function mockList(items = [makeListItem()]) {
  mockedApi.get.mockResolvedValueOnce({ data: { items } })
}

describe('useRecipes', () => {
  beforeEach(() => jest.clearAllMocks())

  it('loads and maps recipes on mount', async () => {
    mockList()
    const { result } = renderHook(() => useRecipes())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).toBeNull()
    expect(result.current.recipes).toHaveLength(1)

    const r = result.current.recipes[0]
    expect(r.id).toBe('r1')
    expect(r.title).toBe('Pasta')
    expect(r.mealType).toBe('dinner')
    expect(r.emoji).toBe('🍽️')
    expect(r.time).toBe(30)
    expect(r.rating).toBe(4)
    expect(r.tags).toEqual(['quick'])
    expect(r.image).toBe('https://example.com/pasta.jpg')
  })

  it('defaults rating to 0 when null', async () => {
    mockList([makeListItem({ rating: null })])
    const { result } = renderHook(() => useRecipes())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.recipes[0].rating).toBe(0)
  })

  it('falls back to dinner for unknown meal type', async () => {
    mockList([makeListItem({ recipe_type: 'brunch' })])
    const { result } = renderHook(() => useRecipes())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.recipes[0].mealType).toBe('dinner')
  })

  it('sets error when list fetch fails', async () => {
    mockedApi.get.mockRejectedValueOnce(new Error('network'))
    const { result } = renderHook(() => useRecipes())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.recipes).toEqual([])
    expect(result.current.error).toBe('Failed to load recipes')
  })

  it('updateRecipe patches the matching recipe', async () => {
    mockList()
    const { result } = renderHook(() => useRecipes())
    await waitFor(() => expect(result.current.loading).toBe(false))

    act(() => {
      result.current.updateRecipe('r1', { saved: true, myRating: 4 })
    })

    const r = result.current.recipes[0]
    expect(r.saved).toBe(true)
    expect(r.myRating).toBe(4)
  })

  it('ensureDetails fetches and applies detail patch', async () => {
    mockList()
    mockedApi.get.mockResolvedValueOnce({ data: makeDetail() })

    const { result } = renderHook(() => useRecipes())
    await waitFor(() => expect(result.current.loading).toBe(false))

    await act(async () => {
      await result.current.ensureDetails('r1')
    })

    const r = result.current.recipes[0]
    expect(r.image).toBe('https://example.com/pasta-hd.jpg')
    expect(r.servings).toBe(4)
    expect(r.steps).toEqual(['Boil water', 'Cook pasta'])
    expect(r.ingredients).toEqual([{ qty: '200g', name: 'pasta' }])
    expect(r.source).toEqual({
      name: 'Bon Appétit',
      url: 'https://bonappetit.com/recipe/pasta',
      domain: 'bonappetit.com',
    })
  })

  it('maps string ingredients in detail', async () => {
    mockList()
    mockedApi.get.mockResolvedValueOnce({
      data: makeDetail({ ingredients: ['salt', 'pepper'] }),
    })

    const { result } = renderHook(() => useRecipes())
    await waitFor(() => expect(result.current.loading).toBe(false))

    await act(async () => {
      await result.current.ensureDetails('r1')
    })

    expect(result.current.recipes[0].ingredients).toEqual([
      { qty: '', name: 'salt' },
      { qty: '', name: 'pepper' },
    ])
  })

  it('ensureDetails does not re-fetch an already-fetched id', async () => {
    mockList()
    mockedApi.get
      .mockResolvedValueOnce({ data: makeDetail() })

    const { result } = renderHook(() => useRecipes())
    await waitFor(() => expect(result.current.loading).toBe(false))

    await act(async () => { await result.current.ensureDetails('r1') })
    await act(async () => { await result.current.ensureDetails('r1') })

    // list + one detail = 2 calls total
    expect(mockedApi.get).toHaveBeenCalledTimes(2)
  })

  it('allows retry after detail fetch fails', async () => {
    mockList()
    mockedApi.get
      .mockRejectedValueOnce(new Error('timeout'))
      .mockResolvedValueOnce({ data: makeDetail() })

    const { result } = renderHook(() => useRecipes())
    await waitFor(() => expect(result.current.loading).toBe(false))

    await act(async () => { await result.current.ensureDetails('r1') })
    await act(async () => { await result.current.ensureDetails('r1') })

    expect(result.current.recipes[0].steps).toEqual(['Boil water', 'Cook pasta'])
  })
})
