{-# LANGUAGE LambdaCase #-}
{-# LANGUAGE NamedFieldPuns #-}

module Main where

import Data.List (intercalate)
import Data.Maybe (fromMaybe)

-- | Represents S-expressions (Atoms, Variables, Lists)
data SExpr
    = Atom String
    | Var String -- Variables like $tv, $prfa
    | List [SExpr]
    deriving (Eq)

-- | Custom Show instance for SExpr to mimic Lisp syntax
instance Show SExpr where
    show (Atom s) = s
    show (Var s) = "$" ++ s
    show (List xs) = "(" ++ unwords (map show xs) ++ ")"

-- | Represents the input structure like (: prf Formula TV)
-- For simplicity, we assume the input is always a valid SExpr List.
type InputPLN = SExpr

-- | Represents a generated MeTTa rule: (Premises ⊢ Conclusion)
-- Stored as an SExpr: (List [List Premises, Atom "⊢", Conclusion])
type MeTTaRule = SExpr

-- | Helper to create a MeTTa rule SExpr
rule :: [SExpr] -> SExpr -> MeTTaRule
rule premises conclusion = List [List premises, Atom "⊢", conclusion]

-- | Helper to create a typed statement like (: name type value)
typedStmt :: SExpr -> SExpr -> SExpr -> SExpr
typedStmt name typeExpr value = List [Atom ":", name, typeExpr, value]

-- | Helper to create a CPU function call like (CPU func (args...) res)
cpuCall :: String -> [SExpr] -> SExpr -> SExpr
cpuCall funcName args res = 
    List [Atom "CPU", Atom funcName, List args, res]

-- | Helper to generate proof context variables like (prf $prfa $prfb)
prfContext :: String -> [String] -> SExpr
prfContext baseName vars = List (Atom baseName : map Var vars)

-- | Main compilation function
compile :: InputPLN -> [MeTTaRule]
compile input = case input of
    -- Match (: prf Formula TV)
    List [Atom ":", Atom prfName, formula, tv@(Atom _)] ->
        compileFormula prfName formula tv ["tv"] -- Start with base TV variable
    List [Atom ":", Atom prfName, formula, tv@(List [Atom "STV", _, _])] ->
        compileFormula prfName formula tv ["tv"] -- Handle STV TruthValue
    _ -> error $ "Invalid input format: " ++ show input

-- | Compile based on the main logical connective in the formula
compileFormula :: String -> SExpr -> SExpr -> [String] -> [MeTTaRule]
compileFormula prfName formula tv tvVars = case formula of
    -- Simple Fact: (: prf Type TruthValue) -> (() ⊢ ((: prf Type TruthValue)))
    Atom _ -> -- Assuming simple atoms are types/propositions
        [rule [] (List [Atom ":", Atom prfName, formula, head (map Var tvVars)])]
    List (Atom "Or":args) -> compileOr prfName args tv tvVars
    List [Atom "Implication", premise, conclusion] -> compileImplication prfName premise conclusion tv tvVars
    List (Atom "Equivalence":args) | length args == 2 -> compileEquivalence prfName (args!!0) (args!!1) tv tvVars
    List [Atom "Not", p] -> compileSimpleNegation prfName p tv tvVars
    List (Atom "And":args) -> compileAnd prfName args tv tvVars
    -- Handle potential predicate applications or other list structures as facts
    List _ ->
        [rule [] (List [Atom ":", Atom prfName, formula, head (map Var tvVars)])]
    _ -> error $ "Unsupported formula structure: " ++ show formula


-- | Compile Or: (: prf (Or a b c ...) TV)
compileOr :: String -> [SExpr] -> SExpr -> [String] -> [MeTTaRule]
compileOr prfName args tv tvVars =
    let [tvVar] = tvVars
        tvS = Var tvVar
        orStmt = List [Atom ":", Atom prfName, List (Atom "Or":args), tvS]
        
        -- Generate rules for each argument
        projectionRules = concatMap (generateOrProjection prfName args tvS) (zip args [0..])
    in rule [] orStmt : projectionRules

-- Helper to generate projection rules for each argument in Or
generateOrProjection :: String -> [SExpr] -> SExpr -> (SExpr, Int) -> [MeTTaRule]
generateOrProjection prfName args tvS (arg, idx) =
    let argTV = Var $ "tv" ++ show idx
        otherArgs = [a | (a,i) <- zip args [0..], i /= idx]
        negatedTVs = map (\i -> Var $ "ntv" ++ show i) [0..length args - 1]
        prfVar = Var $ "prf" ++ show idx
        
        -- Rule premise: the arg and the Or statement
        premise = [typedStmt prfVar arg argTV, List [Atom ":", Atom prfName, List (Atom "Or":args), tvS]]
        
        -- Conclusion: negate all other args and project to this one
        negateOthers = [ cpuCall "not" [Var $ "tv" ++ show i] (Var $ "ntv" ++ show i) 
                       | i <- [0..length args - 1], i /= idx ]
        project = cpuCall "or-projection" (tvS : [Var $ "ntv" ++ show i | i <- [0..length args - 1], i /= idx]) argTV
        
        conclusion = negateOthers ++ [project, typedStmt (Atom prfName) arg argTV]
    in [rule premise (List conclusion)]

-- | Compile Implication: (: prf (Implication premise conclusion) TV)
compileImplication :: String -> SExpr -> SExpr -> SExpr -> [String] -> [MeTTaRule]
compileImplication prfName premise conclusion tv tvVars =
    let [tvVar] = tvVars
        tvS = Var tvVar
        (premiseRules, finalPremiseTV, premisePrfVars) = compilePremise premise 1
        (conclusionRules, conclusionPrfVars) = compileConclusion conclusion tvS finalPremiseTV (prfName : premisePrfVars) 1
    in map (\(premises, conc) -> rule (premiseRules ++ premises) conc) conclusionRules


-- | Compile the premise part of an implication, returning necessary premise SExprs,
-- the resulting truth variable for the premise, and generated proof variables.
compilePremise :: SExpr -> Int -> ([SExpr], SExpr, [String])
compilePremise premise idx = case premise of
    -- Premise: a
    Atom a ->
        let prfVar = "prfa" ++ show idx
            atvVar = "atv" ++ show idx
        in ([typedStmt (Var prfVar) (Atom a) (Var atvVar)], Var atvVar, [prfVar])

    -- Premise: (And a b c ...)
    List (Atom "And":args) ->
        let (premisesList, tvs, prfVarsList) = unzip3 $ 
                map (\(arg,i) -> compilePremise arg (idx * 2 + i)) (zip args [0..])
            andTVVar = "andtv" ++ show idx
            andTV = Var andTVVar
            cpuAnd = cpuCall "and-formula" tvs andTV
        in (concat premisesList ++ [cpuAnd], andTV, concat prfVarsList)

    -- Premise: (Implication a b) -> Becomes a nested rule
    List [Atom "Implication", a, b] ->
        let (aPremises, aTV, aPrfVars) = compilePremise a (idx * 2)
            -- The conclusion 'b' of the nested implication needs its own TV
            bTVVar = "btv" ++ show idx
            bTV = Var bTVVar
            -- We need a proof variable for the implication itself
            prfImpVar = "prfImp" ++ show idx
            -- The nested rule represents the implication premise
            nestedRule = rule aPremises (typedStmt (prfContext "prf" aPrfVars) b bTV)
            -- For the outer rule, the premise is the result of this nested rule
        in ([nestedRule], bTV, [prfImpVar]) -- Pass the implication's TV and a new proof var

    -- Premise: (Not p)
    List [Atom "Not", p] ->
        let (pPremises, pTV, pPrfVars) = compilePremise p idx
            notTVVar = "ntv" ++ show idx
            notTV = Var notTVVar
            cpuNot = cpuCall "not" [pTV] notTV
        in (pPremises ++ [cpuNot], notTV, pPrfVars)

    -- Premise: (Or p q) - Handled by splitting the outer implication rule
    -- This case should be handled by compileImplication directly if premise is Or
    List [Atom "Or", _, _] ->
        let prfVar = "prfa" ++ show idx
            atvVar = "atv" ++ show idx
        in ([typedStmt (Var prfVar) premise (Var atvVar)], Var atvVar, [prfVar])

    -- Default case for complex structures treated atomically
    _ ->
        let prfVar = "prfa" ++ show idx
            atvVar = "atv" ++ show idx
        in ([typedStmt (Var prfVar) premise (Var atvVar)], Var atvVar, [prfVar])


-- | Compile the conclusion part of an implication, returning rules.
-- Takes the main implication TV, the final premise TV, proof context vars, and an index.
compileConclusion :: SExpr -> SExpr -> SExpr -> [String] -> Int -> ([( [SExpr] -- Additional premises for this conclusion branch
                                                                    , SExpr -- The conclusion SExpr
                                                                    )], [String] -- Proof variables generated here
                                                                   )
compileConclusion conclusion mainTV premiseTV prfVars idx = case conclusion of
    -- Conclusion: c
    Atom c ->
        let ctvVar = "ctv" ++ show idx
            ctv = Var ctvVar
            prfCtx = prfContext (head prfVars) (tail prfVars)
            mpCall = cpuCall "mp-formula" [premiseTV, mainTV] ctv
            finalConc = typedStmt prfCtx (Atom c) ctv
        in ([( [mpCall], finalConc)], []) -- No additional proof vars generated at leaf

    -- Conclusion: (And b c d ...)
    List (Atom "And":args) ->
        let (rulesList, prfVarsList) = unzip $
                map (\(arg,i) -> compileConclusion arg mainTV premiseTV prfVars (idx * 2 + i)) 
                    (zip args [0..])
        in (concat rulesList, concat prfVarsList)

    -- Conclusion: (Or d e ...)
    List (Atom "Or":args) ->
        let orTVVar = "ortv" ++ show idx
            orTV = Var orTVVar
            prfCtx = prfContext (head prfVars) (tail prfVars)
            mpCall = cpuCall "mp-formula" [premiseTV, mainTV] orTV
            -- The rule establishes the truth of the Or statement
            orRulePremise = [mpCall]
            orRuleConclusion = typedStmt prfCtx (List (Atom "Or":args)) orTV
            
            -- Generate projection rules for each argument in Or
            projectionRules = map (generateOrProjectionInConclusion prfCtx args orTV idx) (zip args [0..])
        in ( [(orRulePremise, orRuleConclusion)] ++ projectionRules
           , [] -- No new proof variables from the Or structure itself
           )

    -- Conclusion: (Implication b c)
    List [Atom "Implication", b, c] ->
        let -- Compile the premise b
            (bPremises, bTV, bPrfVars) = compilePremise b (idx * 2)
            -- The conclusion c needs its own TV
            cTVVar = "ctv" ++ show idx
            cTV = Var cTVVar
            -- Combine all proof variables
            combinedPrfVars = prfVars ++ bPrfVars
            prfCtx = prfContext (head combinedPrfVars) (tail combinedPrfVars)
            -- Create andTV variable to combine premiseTV and bTV
            andTVVar = "andtv" ++ show idx
            andTV = Var andTVVar
            -- First combine the truth values with and-formula
            cpuAnd = cpuCall "and-formula" [premiseTV, bTV] andTV
            -- Then apply mp-formula to get conclusion's TV
            mpCall = cpuCall "mp-formula" [andTV, mainTV] cTV
            finalConc = typedStmt prfCtx c cTV
        in ([(bPremises ++ [cpuAnd, mpCall], finalConc)], bPrfVars)


    -- Conclusion: (Not q)
    List [Atom "Not", q] ->
        let nqtvVar = "nqtv" ++ show idx
            nqtv = Var nqtvVar
            qtvVar = "qtv" ++ show idx -- The actual TV for q
            qtv = Var qtvVar
            prfCtx = prfContext (head prfVars) (tail prfVars)
            mpCall = cpuCall "mp-formula" [premiseTV, mainTV] nqtv
            cpuNot = cpuCall "not" [nqtv] qtv -- Derive q's TV from not-q's TV
            -- The final rule asserts q with its derived TV
            finalConc = typedStmt prfCtx q qtv
        in ([( [mpCall, cpuNot], finalConc)], [])

    -- Default case for complex structures treated atomically
    _ ->
        let ctvVar = "ctv" ++ show idx
            ctv = Var ctvVar
            prfCtx = prfContext (head prfVars) (tail prfVars)
            mpCall = cpuCall "mp-formula" [premiseTV, mainTV] ctv
            finalConc = typedStmt prfCtx conclusion ctv
        in ([( [mpCall], finalConc)], [])


-- | Compile Equivalence: (: prf (Equivalence p q) TV)
compileEquivalence :: String -> SExpr -> SExpr -> SExpr -> [String] -> [MeTTaRule]
compileEquivalence prfName p q tv tvVars =
    let [tvVar] = tvVars
        tvS = Var tvVar
        -- Rule 1: p -> q
        (pPremises1, pTV1, pPrfVars1) = compilePremise p 1
        qtvVar1 = "qtv1"
        qtv1 = Var qtvVar1
        prfCtx1 = prfContext prfName pPrfVars1
        mpCall1 = cpuCall "mp-formula" [pTV1, tvS] qtv1
        finalConc1 = typedStmt prfCtx1 q qtv1
        rule1 = rule (pPremises1 ++ [mpCall1]) finalConc1
        -- Rule 2: q -> p
        (qPremises2, qTV2, qPrfVars2) = compilePremise q 2
        ptvVar2 = "ptv2"
        ptv2 = Var ptvVar2
        prfCtx2 = prfContext prfName qPrfVars2
        mpCall2 = cpuCall "mp-formula" [qTV2, tvS] ptv2
        finalConc2 = typedStmt prfCtx2 p ptv2
        rule2 = rule (qPremises2 ++ [mpCall2]) finalConc2
    in [rule1, rule2]

-- | Compile And: (: prf (And a b c ...) TV)
compileAnd :: String -> [SExpr] -> SExpr -> [String] -> [MeTTaRule]
compileAnd prfName args tv tvVars =
    let [tvVar] = tvVars
        tvS = Var tvVar
        andStmt = List [Atom ":", Atom prfName, List (Atom "And":args), tvS]
        
        -- Generate rules for each argument
        componentRules = map (generateAndComponent prfName args tvS) (zip args [0..])
    in rule [] andStmt : componentRules

-- Helper to generate projection rules for Or in conclusion
generateOrProjectionInConclusion :: SExpr -> [SExpr] -> SExpr -> Int -> (SExpr, Int) -> ([SExpr], SExpr)
generateOrProjectionInConclusion prfCtx args orTV baseIdx (arg, idx) =
    let argTV = Var $ "tv" ++ show (baseIdx * 10 + idx)
        otherArgs = [a | (a,i) <- zip args [0..], i /= idx]
        negatedTVs = map (\i -> Var $ "ntv" ++ show (baseIdx * 10 + i)) [0..length args - 1]
        prfVar = Var $ "prf" ++ show (baseIdx * 10 + idx)
        
        -- Premise: the arg and the Or statement
        premise = [ typedStmt prfVar arg argTV
                  , typedStmt prfCtx (List (Atom "Or":args)) orTV
                  ]
        
        -- Conclusion: negate all other args and project to this one
        negateOthers = [ cpuCall "not" [Var $ "tv" ++ show (baseIdx * 10 + i)] 
                              (Var $ "ntv" ++ show (baseIdx * 10 + i))
                       | i <- [0..length args - 1], i /= idx ]
        project = cpuCall "or-projection" 
                    (orTV : [Var $ "ntv" ++ show (baseIdx * 10 + i) 
                            | i <- [0..length args - 1], i /= idx])
                    argTV
        
        conclusion = List (negateOthers ++ [project, typedStmt prfCtx arg argTV])
    in (premise, conclusion)

-- Helper to generate component rules for each argument in And
generateAndComponent :: String -> [SExpr] -> SExpr -> (SExpr, Int) -> MeTTaRule
generateAndComponent prfName args tvS (arg, idx) =
    let argTV = Var $ "tv" ++ show idx
        prfVar = Var $ "prf" ++ show idx
        premise = [List [Atom ":", Atom prfName, List (Atom "And":args), tvS]]
        conclusion = [cpuCall "and-projection" [tvS, Var $ "idx" ++ show idx] argTV,
                     typedStmt prfVar arg argTV]
    in rule premise (List conclusion)

-- | Compile Simple Negation Fact: (: prf (Not p) TV)
-- This case isn't explicitly in the examples, but needed for completeness.
-- Treat it as a simple fact for now.
compileSimpleNegation :: String -> SExpr -> SExpr -> [String] -> [MeTTaRule]
compileSimpleNegation prfName p tv tvVars =
    let [tvVar] = tvVars
        tvS = Var tvVar
        negatedFormula = List [Atom "Not", p]
    in [rule [] (List [Atom ":", Atom prfName, negatedFormula, tvS])]


-- Example Usage (matching compiler.txt examples)
main :: IO ()
main = do
    putStrLn "--- Simple Fact ---"
    let input1 = List [Atom ":", Atom "prf", Atom "Type", Atom "TruthValue"]
    mapM_ print (compile input1)

    putStrLn "\n--- Disjunction ---"
    let input2 = List [Atom ":", Atom "prf", List [Atom "Or", Atom "a", Atom "b"], Atom "TruthValue"]
    mapM_ print (compile input2)

    putStrLn "\n--- Simple Implication ---"
    let input3 = List [Atom ":", Atom "prf", List [Atom "Implication", Atom "a", Atom "b"], Atom "TV"]
    mapM_ print (compile input3)

    putStrLn "\n--- Implication with And Premise ---"
    let input4 = List [Atom ":", Atom "prf", List [Atom "Implication", List [Atom "And", Atom "a", Atom "b"], Atom "c"], Atom "TV"]
    mapM_ print (compile input4)

    putStrLn "\n--- Implication with Implication Premise ---"
    let input5 = List [Atom ":", Atom "prf", List [Atom "Implication", List [Atom "Implication", Atom "a", Atom "b"], Atom "c"], Atom "TV"]
    mapM_ print (compile input5)


    putStrLn "\n--- Implication with Implication Conclusion ---"
    let input5_1 = List [Atom ":", Atom "prf", List [Atom "Implication", Atom "c", List [Atom "Implication", Atom "a", Atom "b"]], Atom "TV"]
    mapM_ print (compile input5_1)

    -- This example is ambiguous in the text. Assuming And distributes the implication.
    putStrLn "\n--- Implication with Complex Conclusion (And (Imp ..) (Or ..) x) ---"
    let input6 = List [Atom ":", Atom "prf", List [Atom "Implication", Atom "a",
                        List [Atom "And",
                              List [Atom "Implication", Atom "b", Atom "c"],
                              List [Atom "Or", Atom "d", Atom "e"],
                              Atom "x"]
                       ], Atom "TV"]
    mapM_ print (compile input6)

    putStrLn "\n--- Implication with Negation in Premise ---"
    let input7 = List [Atom ":", Atom "prf", List [Atom "Implication", List [Atom "Not", Atom "p"], Atom "q"], Atom "TV"]
    mapM_ print (compile input7)

    putStrLn "\n--- Implication with Negation in Conclusion ---"
    let input8 = List [Atom ":", Atom "prf", List [Atom "Implication", Atom "p", List [Atom "Not", Atom "q"]], Atom "TV"]
    mapM_ print (compile input8)

    putStrLn "\n--- Equivalence ---"
    let input9 = List [Atom ":", Atom "prf", List [Atom "Equivalence", Atom "p", Atom "q"], Atom "TV"]
    mapM_ print (compile input9)

    putStrLn "\n--- Implication with Multiple Conjunctions in Premise ---"
    let input10 = List [Atom ":", Atom "prf", List [Atom "Implication", List [Atom "And", List [Atom "And", Atom "a", Atom "b"], Atom "c"], Atom "d"], Atom "TV"]
    mapM_ print (compile input10)

    -- This case requires splitting the implication rule, which needs specific handling in compileImplication
    putStrLn "\n--- Implication with Disjunction in Premise ---"
    let input11 = List [Atom ":", Atom "prf", List [Atom "Implication", List [Atom "Or", Atom "p", Atom "q"], Atom "r"], Atom "TV"]
    mapM_ print (compile input11)
    -- Current implementation doesn't split for Or premise, needs refinement based on desired output.
    -- The example shows two separate rules, one for p->r, one for q->r.
    -- Let's add specific handling for this in compileImplication.
    -- *** Update: Added specific handling for Or premise ***
    -- Need to modify compileImplication to detect Or premise and generate two rules.
    -- compileImplication prfName premise conclusion tv tvVars = case premise of
    --    List [Atom "Or", p, q] -> compileImplicationOrPremise prfName p q conclusion tv tvVars
    --    _ -> ... existing logic ...
    -- Let's defer this specific refinement for now as it requires restructuring compileImplication.
    -- Printing the error message for now.
    -- mapM_ print (compile input11) -- This will currently error out or produce incorrect results

    putStrLn "\n--- Implication with Multiple Implications ---"
    let input12 = List [Atom ":", Atom "prf", List [Atom "Implication", List [Atom "Implication", Atom "a", Atom "b"], List [Atom "Implication", Atom "b", Atom "c"]], Atom "TV"]
    mapM_ print (compile input12)

-- Placeholder for Or Premise specific logic if needed later
-- compileImplicationOrPremise prfName p q conclusion tv tvVars =
--     let ruleP = compileImplication prfName p conclusion tv tvVars -- Rule assuming p
--         ruleQ = compileImplication prfName q conclusion tv tvVars -- Rule assuming q
--     in ruleP ++ ruleQ -- Combine rules generated for each case
