import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import MealsTab from './MealsTab'
import { useRecipes } from '@/hooks/useRecipes'
import { useGroceryList } from '@/hooks/useGroceryList'
import type { Recipe } from '@/types/meals'

jest.mock('@/hooks/useRecipes', () => ({
  useRecipes: jest.fn(),
}))

jest.mock('@/hooks/useGroceryList', () => ({
  useGroceryList: jest.fn(),
}))

jest.mock('./RecipeCard', () => ({
  __esModule: true,
  default: ({ recipe }: { recipe: Recipe }) => <div>{recipe.title}</div>,
}))

jest.mock('./RecipeSheet', () => ({
  __esModule: true,
  default: () => null,
}))

jest.mock('./meals.css', () => ({}))

const mockedUseRecipes = useRecipes as jest.MockedFunction<typeof useRecipes>
const mockedUseGroceryList = useGroceryList as jest.MockedFunction<typeof useGroceryList>

const recipe: Recipe = {
  id: 'recipe-1',
  title: 'Chicken soup',
  emoji: '🍽️',
  image: '',
  mealType: 'dinner',
  time: 30,
  rating: 4.5,
  myRating: 0,
  saved: false,
  cooked: false,
  cookedCount: 0,
  lastCooked: null,
  servings: 2,
  description: '',
  ingredients: [],
  steps: [],
  source: { name: null, url: null, domain: null },
  tags: ['quick'],
}

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.search}</output>
}

function renderMeals(initialEntry = '/meals') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <MealsTab />
      <LocationProbe />
    </MemoryRouter>,
  )
}

function recipesHookResult(
  overrides: Partial<ReturnType<typeof useRecipes>> = {},
): ReturnType<typeof useRecipes> {
  return {
    recipes: [recipe],
    total: 50,
    loading: false,
    error: null,
    updateRecipe: jest.fn(),
    ensureDetails: jest.fn(),
    toggleLike: jest.fn(),
    toggleCooked: jest.fn(),
    rateRecipe: jest.fn(),
    ...overrides,
  }
}

describe('MealsTab search state', () => {
  beforeEach(() => {
    mockedUseRecipes.mockReturnValue(recipesHookResult())
    mockedUseGroceryList.mockReturnValue({
      list: { active: [], history: [] },
      loading: false,
      error: null,
      refetch: jest.fn(),
      addItem: jest.fn(),
      markBought: jest.fn(),
      restoreItem: jest.fn(),
      removeItem: jest.fn(),
      clearHistory: jest.fn(),
      addFromRecipe: jest.fn(),
    })
  })

  it('builds the server search specification from the URL', () => {
    renderMeals(
      '/meals?q=chicken&meal=dinner&meal=lunch&maxTime=30&liked=true&cooked=true&sort=fastest&page=2',
    )

    expect(mockedUseRecipes).toHaveBeenCalledWith({
      text: 'chicken',
      mealTypes: ['dinner', 'lunch'],
      labels: [],
      ingredients: [],
      maxTotalMinutes: 30,
      liked: true,
      cooked: true,
      sort: 'fastest',
      page: 2,
      limit: 24,
    })
  })

  it('writes search and personal filters to the URL and resets pagination', async () => {
    renderMeals('/meals?page=3')

    fireEvent.change(screen.getByPlaceholderText('Search recipes — title, tag, anything…'), {
      target: { value: 'pasta' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Liked' }))
    fireEvent.click(screen.getByRole('button', { name: 'Already cooked' }))

    await waitFor(() => {
      const location = screen.getByTestId('location').textContent ?? ''
      expect(location).toContain('q=pasta')
      expect(location).toContain('liked=true')
      expect(location).toContain('cooked=true')
      expect(location).not.toContain('page=')
    })
  })

  it('removes difficulty and exposes only real personal filters', () => {
    renderMeals()

    expect(screen.queryByText('Difficulty')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Liked' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: 'Already cooked' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('shows a failed-search error while retaining previous results', () => {
    mockedUseRecipes.mockReturnValue(recipesHookResult({ error: 'Failed to load recipes' }))

    renderMeals('/meals?q=soup')

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Failed to load recipes. Showing previous results.',
    )
    expect(screen.getByText(recipe.title)).toBeInTheDocument()
  })
})
