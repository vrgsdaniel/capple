export interface HouseholdMember {
  id: string
  name: string
  avatar_url: string | null
}

export interface HouseholdMembers {
  me: HouseholdMember
  others: HouseholdMember[]
}