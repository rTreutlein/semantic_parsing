(= (rb) (: ModusPonens
                (-> (ImplicationLink $p $q) $p $q)))

(= (rb) (: ModusPonens
                (-> (InheritanceLink $p $q) $p $q)))

; Hypothetical Syllogism
(= (rb) (: HypotheticalSyllogism
                (-> (ImplicationLink $p $q) (ImplicationLink $q $r)
                    (ImplicationLink $p $r))))

; Disjunctive Syllogism (Left)
(= (rb) (: DisjunctiveSyllogism
                (-> (OrLink $p $q) (NotLink $p) $q)))

; Disjunctive Syllogism (Right)
(= (rb) (: DisjunctiveSyllogism
                (-> (OrLink $p $q) (NotLink $q) $p)))

; Conjunction Introduction
(= (rb) (: ConjunctionIntroduction
                (-> $p $q (AndLink $p $q))))

; Conjunction Elimination (Left)
(= (rb) (: ConjunctionEliminationLeft
                (-> (AndLink $p $q) $p)))

; Conjunction Elimination (Right)
(= (rb) (: ConjunctionEliminationRight
                (-> (AndLink $p $q) $q)))

; Disjunction Introduction
(= (rb) (: DisjunctionIntroduction
                (-> $p $q (OrLink $p $q))))
