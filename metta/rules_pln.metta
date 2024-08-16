!(add-atom &kb (: ModusPonens
                (-> (ImplicationLink $p $q)
                    (-> "$p"
                    "$q"))))

!(add-atom &kb (: ModusPonens
                (-> (InheritanceLink $p $q)
                    (-> "$p"
                    "$q"))))


; Hypothetical Syllogism
!(add-atom &kb (: HypotheticalSyllogism
                (ImplicationLink
                    (AndLink
                        (ImplicationLink (VariableNode "$p") (VariableNode "$q"))
                        (ImplicationLink (VariableNode "$q") (VariableNode "$r"))
                    )
                    (ImplicationLink (VariableNode "$p") (VariableNode "$r")))))

; Disjunctive Syllogism
!(add-atom &kb (: DisjunctiveSyllogism
                (ImplicationLink
                    (AndLink
                        (OrLink (VariableNode "$p") (VariableNode "$q"))
                        (NotLink (VariableNode "$p"))
                    )
                    (VariableNode "$q"))))

; Conjunction Introduction
!(add-atom &kb (: ConjunctionIntroduction
                (ImplicationLink
                    (AndLink
                        (VariableNode "$p")
                        (VariableNode "$q")
                    )
                    (AndLink (VariableNode "$p") (VariableNode "$q")))))

; Conjunction Elimination (Left)
!(add-atom &kb (: ConjunctionEliminationLeft
                (ImplicationLink
                    (AndLink (VariableNode "$p") (VariableNode "$q"))
                    (VariableNode "$p"))))

; Conjunction Elimination (Right)
!(add-atom &kb (: ConjunctionEliminationRight
                (ImplicationLink
                    (AndLink (VariableNode "$p") (VariableNode "$q"))
                    (VariableNode "$q"))))

; Disjunction Introduction (Left)
!(add-atom &kb (: DisjunctionIntroductionLeft
                (ImplicationLink
                    (VariableNode "$p")
                    (OrLink (VariableNode "$p") (VariableNode "$q")))))

; Disjunction Introduction (Right)
!(add-atom &kb (: DisjunctionIntroductionRight
                (ImplicationLink
                    (VariableNode "$q")
                    (OrLink (VariableNode "$p") (VariableNode "$q")))))
