!(add-atom &kb (: ModusPonens
                (-> (ImplicationLink $p $q) $p $q)))

!(add-atom &kb (: ModusPonens
                (-> (InheritanceLink $p $q) $p $q)))

; Hypothetical Syllogism
!(add-atom &kb (: HypotheticalSyllogism
                (-> (ImplicationLink $p $q) (ImplicationLink $q $r)
                    (ImplicationLink $p $r))))

; Disjunctive Syllogism (Left)
!(add-atom &kb (: DisjunctiveSyllogism
                (-> (OrLink $p $q) (NotLink $p) $q)))

; Disjunctive Syllogism (Right)
!(add-atom &kb (: DisjunctiveSyllogism
                (-> (OrLink $p $q) (NotLink $q) $p)))

; Conjunction Introduction
!(add-atom &kb (: ConjunctionIntroduction
                (-> $p $q (AndLink $p $q))))

; Conjunction Elimination (Left)
!(add-atom &kb (: ConjunctionEliminationLeft
                (-> (AndLink $p $q) $p)))

; Conjunction Elimination (Right)
!(add-atom &kb (: ConjunctionEliminationRight
                (-> (AndLink $p $q) $q)))

; Disjunction Introduction
!(add-atom &kb (: DisjunctionIntroductionLeft
                (-> $p $q (OrLink $p $q))))
